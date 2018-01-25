import os
import random
from keras.preprocessing import image
import numpy as np
from logger import logger
from vocab import vocabBuilder

DATA_DIR = '/home/gagan.cs14/btp'
GITBRANCH = os.popen('git branch | grep "*"').read().split(" ")[1][:-1] 
WORKING_DIR = "/home/gagan.cs14/btp_"+GITBRANCH
BADLOGS = WORKING_DIR+"/badlogs.txt"

def badLogs(msg):
    logger.debug(msg)
    with open(BADLOGS,"a") as f:
        f.write(msg)

class Preprocessor:
    def __init__(self):
        self.vHandler,self.vocab = vocabBuilder(DATA_DIR, WORKING_DIR)

    def imageToVec(self, fname):
        NEED_W = 224
        NEED_H = 224
        img = image.load_img(fname, target_size=(NEED_H, NEED_W))
        x = image.img_to_array(img)
        x /= 255.
        x -= 0.5
        x *= 2.
        return x

    '''
    Either convert videos from ids or frame file names
    '''
    def videoToVec(self, _id = None, fnames = None):
        assert (_id is None) ^ (fnames is None)
        if fnames is None:
            fnames = self.vHandler.get_frames(_id = _id, logs = False)
        if fnames is None:
            return None
        content = []
        for fname in fnames:
            content.append(self.imageToVec(fname))
        return content

    def get_video_content(self, vfname):
        print vfname
        fnames = self.vHandler.get_frames(sfname = vfname)
        return self.videoToVec(fnames = fnames)

    def get_video_caption(self, _id):
        data = self.vHandler.getCaptionData()
        cur_caption = data[_id]
        captionIn = self.vocab.get_caption_encoded(cur_caption, True, True, False)
        captionOut = self.vocab.get_caption_encoded(cur_caption, False, False, True)
        vid = self.videoToVec(_id)
        if vid is None:
            return None
        return np.asarray([vid,captionIn,captionOut])

    def datas_from_ids(self, idlst):
        logger.debug("\n Loading Video/Captions for ids : %s" % str(idlst))
        vids   = []
        capIn  = []
        capOut = []
        for _id in idlst:
            _vid, _capIn, _capOut = self.get_video_caption(_id)
            vids.append(_vid)
            capIn.append(_capIn)
            capOut.append(_capOut)
            return [[np.asarray(capIn),np.asarray(vids)],np.asarray(capOut)]
 
    '''
    typeSet 0:Training dataset, 1: Validation dataset, 2: Test Dataset
    '''
    def data_generator(self, batch_size, start=0, typeSet = 0):
        if typeSet == 0:
            ids = self.vHandler.getTrainingIds()
        elif typeSet == 1:
            ids = self.vHandler.getValidationIds()
        elif typeSet == 2:
            ids = self.vHandler.getTestIds()
        else:
            assert False
        count = (len(ids))/batch_size
        if start == -1:
            start = random.randint(0,count)
        logger.debug("Max Batches of type %d : %d " % (typeSet, count))
        assert count > 0
        start = start % count
        while True:
            idlst = ids[start*batch_size:(start+1)*batch_size]
            data = self.datas_from_ids(idlst)
            ndata = []
            for d in data:
                if d is not None:
                    ndata.append(d)
            if len(ndata) > 0:
                yield ndata
            start = (start + 1)%count
