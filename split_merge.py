import os
import sys
import webknossos as wk
import numpy as np
from webknossos.geometry import BoundingBox, Mag, Vec3Int
from time import gmtime, strftime
import fastremap
from tqdm import tqdm
from omegaconf import OmegaConf


def main(conf):
    token = conf.token
    path = conf.revision_path  # WQ
    scale = tuple([x for x in conf.scale])  # (5.0, 5.0, 50.0)
    segmentation_layer = conf.segmentation_layer  #     "segmentations"
    online_dataset = conf.online_dataset  # "W-Q_x0_y0_z0_2022-01-02_00-43-18"
    online_team = conf.online_team  # "4fd6473e68256c0a"
    annotation_url = conf.annotation_url  # "https://webknossos.org/annotations/Explorational/61d5c797010000b500b3a085"

    with wk.webknossos_context(url="https://webknossos.org", token=token):
        # Get the dataset first
        if os.path.exists(path):
            dataset = wk.Dataset(path, scale=scale, exist_ok=True)
        else:
            print("Downloading the dataset. This will take a while.")
            dataset = wk.Dataset.download(
            online_dataset,  # "W-Q_x0_y0_z0_2022-01-02_00-43-18",  # zebrafish_vertebra_250um",
            online_team,  # "4fd6473e68256c0a",
            layers=["images", segmentation_layer],  # , "Volume Layer"],
            mags=[Mag("1")],
            path=path,
        )
        annotation = wk.Annotation.download(annotation_url)
        time_str = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
        new_dataset_name = annotation.dataset_name + f"_segmented_{time_str}"
        new_dataset = wk.Dataset(new_dataset_name, scale=scale)

        # Load skeletons (ideally get this through annotation api in the future?)
        nml = annotation.skeleton

        # Start merging annotations into base
        print("Loading data into memory")
        volume_annotation_layer = annotation.export_volume_layer_to_dataset(new_dataset)
        print(volume_annotation_layer.bounding_box)
        volume_annotation_mag = volume_annotation_layer.mags[wk.Mag(1)]
        # volume_annotation_mag = volume_annotation_layer.get_best_mag()

        # Overwrite base annotation with new annotations
        segmentation_mag = dataset.layers["segmentations"].mags[wk.Mag(1)]
        segmentation_data = segmentation_mag.read()
        print("Overwriting base annotation. This could take a while.")
        for info in volume_annotation_mag.get_bounding_boxes_on_disk():
            offset = info.topleft
            size = info.size
            data = volume_annotation_mag.read(offset, size)
            segmentation_data[
                0,
                offset[0]: offset[0] + size[0],
                offset[1]: offset[1] + size[1],
                offset[2]: offset[2] + size[2]]
            segmentation_mag.write(data, offset)
            print(f"Overwrote bbox {offset} {size}")
  
        # Merge through skeletions
        edits = {}  # A dict with a list per entry
        for tree in nml._child_graphs:  # nml.trees() is a flattened iterator of all trees
            name_str = tree.graph["name"]
            name = name_str.split("_")[0]
            command = name_str.split("_")[1]
            coords = [np.asarray(x.position).astype(int) for x in tree.nodes]
            if len(coords):
                segto = segmentation_data[0, coords[0][0], coords[0][1], coords[0][2]]
                segfrom = segmentation_data[0, coords[1][0], coords[1][1], coords[1][2]]
                if name not in edits:  # Sort the commands into different edits
                    edits[name] = {}
                edits[name][command] = [{segfrom: segto}, coords]
        for name, commands in tqdm(edits.items(), total=len(edits), desc="Merging"):
            pos = commands["merge"]
            segmentation_data = fastremap.remap(segmentation_data, pos[0], preserve_missing_labels=True)
            if len(commands) == 2:
                # Pos (merge) and neg (split) control
                neg = commands["split"]
                negfrom = segmentation_data[0, neg[1][0][0], neg[1][0][1], neg[1][0][2]]
                negto = segmentation_data[0, neg[1][1][0], neg[1][1][1], neg[1][1][2]]
                if negfrom == negto:
                    print("Segment id bled from {} to {} in negative control.".format(neg[1][0], neg[1][1]))
                else:
                    pos_0 = [x for x in pos[0].keys()][1]
                    print("Segment id {} successfully propogated.".format(pos_0))

        # Overwrite annotations
        # dataset.delete_layer(segmentation_layer)
        new_segmentation_layer = new_dataset.add_layer(
            segmentation_layer,
            wk.SEGMENTATION_CATEGORY,
            volume_annotation_layer.dtype_per_channel,
            largest_segment_id=int(segmentation_data.max())
        )
        new_segmentation_mag = new_segmentation_layer.add_mag("1")
        new_segmentation_mag.write(segmentation_data)
        new_segmentation_mag.compress()
        new_segmentation_layer.downsample()
        url = new_dataset.upload(
            layers_to_link=[
                wk.LayerToLink(
                    organization_id=online_team,
                    dataset_name=online_dataset,
                    layer_name="images",
                )
            ]
        )
        print("Uploaded new base annotation to: {}".format(url)) 


if __name__ == '__main__':
    conf = sys.argv[1]  # "configs/W-Q.yml"
    conf = OmegaConf.load(conf)
    main(conf)

