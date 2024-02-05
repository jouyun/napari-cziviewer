import pandas as pd
import numpy as np
import napari
import czifile
import glob
import napari
import skimage as ski
import xml.etree.ElementTree as ET

class CziViewer:
    def __init__(self, viewer):
        self.viewer = viewer
    
    def truncate_img(self, overview_img):
        A = np.squeeze(overview_img)[0]

        xmin = np.where(np.max(A, axis=0))[0][0]
        xmax = np.where(np.max(A, axis=0))[0][-1]
        ymin = np.where(np.max(A, axis=1))[0][0]
        ymax = np.where(np.max(A, axis=1))[0][-1]

        return overview_img[:, ymin:ymax, xmin:xmax], xmin, ymin

    def get_tile_center(self, fname):
        xml_data = czifile.CziFile(fname).metadata()
        root = ET.fromstring(xml_data)
        positions = [elem.text for elem in root.findall('Metadata/Information/Image/Dimensions/S/Scenes/Scene/CenterPosition')]
        positions = np.array([np.array(p.split(',')).astype(np.float32) for p in positions])
        return positions

    def get_resolution(self, fname):
        xml_data = czifile.CziFile(fname).metadata()
        root = ET.fromstring(xml_data)
        resolutions = [elem.text for elem in root.findall('Metadata/Scaling/Items/Distance/Value')]
        return np.array(resolutions).astype(float)[0:2] * 1E6

    def get_true_position(self, fname):
        xml_data = czifile.CziFile(fname).metadata()
        first_pos = xml_data.find('<MeasurementPosition')
        second_pos = xml_data.find('<MeasurementPosition', first_pos+1)
        third_pos = xml_data.find('<MeasurementPosition', second_pos+1)

        z = xml_data[first_pos-100:first_pos].split('\n')[-2].split('>')[1].split('<')[0]
        y = xml_data[second_pos-100:second_pos].split('\n')[-2].split('>')[1].split('<')[0]
        x = xml_data[third_pos-100:third_pos].split('\n')[-2].split('>')[1].split('<')[0]
        rtn = np.array([z,y,x]).astype(float)
        return rtn[1:]
        
    def load_overview(self, fname, idx=0):
        self.overview = fname
        self.full_img = czifile.imread(fname)
        tmp_img, self.xmin, self.ymin = self.truncate_img(np.squeeze(self.full_img[0]))
        self.c0_shape = np.array(tmp_img.shape[-2:])
        self.overview_img = np.squeeze(self.full_img)
        self.overview_res = self.get_resolution(fname)
        self.overview_centroid = self.get_tile_center(fname)[idx]
        
        self.viewer.layers.clear()
        contrast_limits = [0, 65535]
        if len(self.overview_img.shape)==2:
            self.viewer.add_image(np.squeeze(self.overview_img), name='Overview', scale=self.overview_res, contrast_limits=contrast_limits)
        if len(self.overview_img.shape)==3:
            self.viewer.add_image(np.squeeze(self.overview_img), scale=self.overview_res, channel_axis=0, contrast_limits=contrast_limits, name=['C' + str(i) + '_Overview' for i in range(self.overview_img.shape[0])])
        if len(self.overview_img.shape)==4:
            self.viewer.add_image(np.squeeze(self.overview_img).max(axis=0), scale=self.overview_res, channel_axis=0, contrast_limits=contrast_limits, name=['C' + str(i) +'_Overview' for i in range(self.overview_img.shape[1])])

        default_colors = ['magenta', 'gray', 'yellow', 'green', 'blue']
        for i, layer in enumerate(self.viewer.layers):
            if i<5:
                layer.colormap = default_colors[i]
            if i==1:
                layer.visible = False

        self.viewer.scale_bar.visible = True
        self.viewer.scale_bar.unit = "um"
    
    def load_zoom(self, fname, idx=0, composite=False, name=None):
        zoom_full_img = czifile.imread(fname)
        zoom_img = np.squeeze(zoom_full_img)
        zoom_res = self.get_resolution(fname)
        print(fname)
        zoom_centroid = self.get_true_position(fname)
        zoom_shape = np.array(zoom_img.shape)[-2:]
        
        self.overview_centroid = self.get_tile_center(self.overview)[idx]

        overview_ctr_microns = self.c0_shape / 2 * self.overview_res
        zoom_ctr_microns = zoom_shape / 2 * zoom_res
        translation = overview_ctr_microns - zoom_ctr_microns
        translation = translation - 1*(self.overview_centroid - zoom_centroid)[::-1]
        
        translation = translation + np.array([self.ymin*self.overview_res[0], self.xmin*self.overview_res[0]])

        # AD HOC CORRECTION for 5X vs 63X
        translation = translation - 50

        fname = fname.replace('\\', '/')
        if (name is None) | (name == ''):
            name = fname.split('/')[-1]
        #contrast_limits = [0, np.max(zoom_img)]
        contrast_limits = [0, 65535]

        if len(zoom_img.shape)==2:
            self.viewer.add_image(zoom_img, scale=zoom_res, translate=translation, name=name, contrast_limits=contrast_limits)
        if len(zoom_img.shape)==3:
            self.viewer.add_image(zoom_img, scale=zoom_res, translate=translation, name=name, contrast_limits=contrast_limits)
        if len(zoom_img.shape)==4:
            if composite:
                self.viewer.add_image(zoom_img, scale=zoom_res, channel_axis=0, translate=translation, contrast_limits=contrast_limits, name=['C' + str(i) +'_' + name for i in range(zoom_img.shape[0])])
            else:
                self.viewer.add_image(zoom_img, scale=zoom_res, translate=translation, name=name, contrast_limits=contrast_limits)
    
        self.focus_on(self.viewer.layers[-1])
        
    def focus_on(self, layer):
        img_center_offset_x = layer.scale[-1] * layer.data.shape[-1]/2
        img_center_offset_y = layer.scale[-2] * layer.data.shape[-2]/2

        trans = layer.translate
        self.viewer.camera.center = (0,trans[-2]+img_center_offset_y, trans[-1]+img_center_offset_x)
        self.viewer.camera.zoom = 4
        
    def select_on(self):
        current = np.array(self.viewer.camera.center[-2:])

        distances = []
        overview_channels = 0
        for layer in self.viewer.layers:
            if layer.name.endswith('Overview'):
                overview_channels += 1
            else:
                trans = np.array(layer.translate[-2:])
                scale = np.array(layer.scale[-2:])
                shape = np.array(layer.data.shape[-2:])
                trans = trans + (shape/2 * scale)
                distance = np.linalg.norm(trans-current)
                distances.append(distance)

        indices = np.array(np.where(distances==np.min(distances))[0]) + overview_channels
        myset = set({self.viewer.layers[i] for i in indices})
        self.viewer.layers.selection.active = self.viewer.layers[indices[0]]
        self.viewer.layers.selection.update(myset)