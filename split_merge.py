import os
import webknossos as wk
import numpy as np
from webknossos.geometry import BoundingBox, Mag, Vec3Int
from time import gmtime, strftime
import fastremap
from tqdm import tqdm


token = "UTUOQJvbbyRFbD_NSnTMig"
path = "WQ"
scale = (5.0, 5.0, 50.0)
segmentation_layer = "segmentations"
with wk.webknossos_context(url="https://webknossos.org", token=token):
    # Get the dataset first
    if os.path.exists(path):
        dataset = wk.Dataset(path, scale=scale, exist_ok=True)
    else:
        dataset = wk.Dataset.download(
            "W-Q_x0_y0_z0_2022-01-02_00-43-18",  # zebrafish_vertebra_250um",
            "4fd6473e68256c0a",
            layers=["images", segmentation_layer],  # , "Volume Layer"],
            mags=[Mag("1")],
            path=path,
        )
    annotation = wk.Annotation.download(
        "https://webknossos.org/annotations/Explorational/61d5c797010000b500b3a085"
    )
    time_str = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
    new_dataset_name = annotation.dataset_name + f"_segmented_{time_str}"
    new_dataset = wk.Dataset(new_dataset_name, scale=scale)

    # Load skeletons (ideally get this through annotation api in the future?)
    nml = annotation.skeleton

    # Start merging annotations into base
    print("Loading data into memory")
    volume_annotation_layer = annotation.save_volume_annotation(new_dataset)
    print(volume_annotation_layer.bounding_box)
    volume_annotation_mag = volume_annotation_layer.mags[wk.Mag(1)]

    # Overwrite base annotation with new annotations
    segmentation_mag = dataset.layers["segmentations"].mags[wk.Mag(1)]
    segmentation_data = segmentation_mag.read()
    for offset, size in volume_annotation_mag.get_bounding_boxes_on_disk():
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
    for tree in nml._children:  # nml.trees() is a flattened iterator of all trees
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
                neg_0 = [x for x in neg[0].keys()][0]
                neg_1 = [x for x in neg[0].keys()][1]
                print("Segment id bled from {} to {} in negative control.".format(neg_0, neg_1))
            else:
                pos_0 = [x for x in pos[0].keys()][1]
                print("Segment id {} successfully propogated.".format(pos_0))
            negid = neg.values()[1]

    # Overwrite annotations
    dataset.delete_layer(segmentation_layer)
    segmentation_layer = dataset.add_layer(
        segmentation_layer,
        wk.SEGMENTATION_CATEGORY,
        volume_annotation_layer.dtype_per_channel,
        largest_segment_id=segmentation_data.max()
    )
    segmentation_mag = segmentation_layer.add_mag("1")
    segmentation_mag.write(dsegmentation_data)
    segmentation_mag.compress()
    segmentation_layer.downsample()
    url = dataset.upload()
    print("Uploaded new base annotation to: {}".format(url)) 

