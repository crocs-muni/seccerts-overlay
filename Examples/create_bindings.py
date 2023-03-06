import urllib.request
import hashlib
from datetime import datetime
import json

metadataObjs = [
    {
        "measurementTool" : "JCAlgtest",
        "measurementAuthor" : "CROCS",
        "certificateIds" : ["SERTIT-116"],
        "metaDataURI" : "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Feitian_JavaCOS_3.0.4____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1557852970194__3b_fc_18_00_00_81_31_80_45_90_67_46_4a_00_64_16_06_00_00_00_00_1e.csv",
        "version" : "1.0"
    },
    {
        "measurementTool" : "JCAlgtest",
        "measurementAuthor" : "CROCS",
        "certificateIds" : ["NSCIB-CC-0031318-CR2", "NSCIB-CC-0031318-CR3"],
        "metaDataURI" : "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Infineon_SECORA_ID_X_Batch_16072021_SALES____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1627630268599__3b_88_80_01_00_00_00_11_77_81_c3_00_2d_(provided_by_Thoth).csv",
        "version" : "1.0"
    }
]

def getMetadataMetadata(uri):
    metadataFilePath = "metadata.csv"
    urllib.request.urlretrieve(uri, metadataFilePath)
    sha256 = hashlib.sha256()
    BUFF_SIZE = 65536
    with open(metadataFilePath, 'rb') as f:
        data = f.read(BUFF_SIZE)
        while data:
            sha256.update(data)
            data = f.read(BUFF_SIZE)
    
    return {
        "metaDataSha256" : "{0}".format(sha256.digest()),
        "timeStamp" : datetime.now().__str__(),
    }

def createMetadataBinding(metadataObj):
    return getMetadataMetadata(metadataObj["metaDataURI"]) | metadataObj

def createBindingFile(bindingsData, bindingsFilePath):
    bindings = list(map(createMetadataBinding, bindingsData))
    with open(bindingsFilePath, 'w') as f:
        f.write(json.dumps(bindings))
    

if __name__ == "__main__":
    createBindingFile(metadataObjs, "json_example.json")
    