import webknossos as wk
from webknossos.geometry import BoundingBox, Mag

token = "UTUOQJvbbyRFbD_NSnTMig"
with wk.webknossos_context(url="https://webknossos.org", token=token):
    train_soma_dataset = wk.download_dataset(
        "zebrafish_vertebra_250um",  # zebrafish_vertebra_250um",
        "b2275d664e4c2a96",
        bbox=BoundingBox((10533, 7817, 3547), (1152, 1152, 384)),
        layers=["color"],  # , "Volume Layer"],
        mags=[Mag("1")],
        path="../zebrafish",
    )

    print(f"Sucessfully downloaded: zebrafish")

