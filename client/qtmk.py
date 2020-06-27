from glob import glob
import os.path as op
from lxml import etree
import subprocess

def mk():
    for ui in glob(op.join(op.dirname(__file__),"**","*.ui"),recursive=True):
        #find any qrc file referenced in the ui files
        content = etree.parse(ui).getroot()
        res = content.find("resources")
        qrcs = []
        if res is not None:
            dirname = op.dirname(ui)
            for file in [x.attrib.get("location") for x in res.findall("include")]:
                if file.endswith(".qrc"): qrcs.append(op.join(dirname, file))
        #build qrc python files
        for qrc in qrcs: subprocess.call(["pyrcc5", qrc, "-o", qrc.replace(".qrc", "RC.py")])

        #build ui python files
        subprocess.call(["pyuic5", ui, "--resource-suffix", "RC", "-o", ui.replace(".ui", "_ui.py")])

if __name__ == "__main__": mk()