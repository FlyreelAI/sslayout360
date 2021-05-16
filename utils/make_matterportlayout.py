import os
import json
import argparse
import numpy as np


parser = argparse.ArgumentParser(
    description='Create MatterportLayout train, val, test datasets with layout annotations '\
                'converted from .json to .txt format following HorizonNet notation',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('--img-root', required=True,
                    help='path to Matterport3D image directory')
parser.add_argument('--ann-root', required=True,
                    help='path to layout annotation directory')
parser.add_argument('--dataset', required=True,
                    help='path to `train`, `val`, and `test` .txt data splits')
parser.add_argument('--split-name', required=True,
                    help='indicator for `train`, `val`, `test`')
parser.add_argument('--camera-height', default=1.6, type=float,
                    help='distance between camera and floor in meters')
parser.add_argument('--img-width', default=1024, type=int,
                    help='image width')
parser.add_argument('--img-height', default=512, type=int,
                    help='image height')
parser.add_argument('--out-dir', default='./mp3d_layout',
                    help='out directory with `img` and `label_cor` subdirectories')


def json2txt(json_path, txt_path, args):
    gt = json.load(open(json_path, 'r'))
    assert gt['cameraHeight'] == args.camera_height
    u = np.array([pts['coords'][0] for pts in gt['layoutPoints']['points']])
    u = u * args.img_width
    c = np.array([pts['xyz'] for pts in gt['layoutPoints']['points']])
    c = np.sqrt((c**2)[:, [0, 2]].sum(1))

    vfloor = np.arctan2(-args.camera_height, c)
    vceil = np.arctan2(-args.camera_height + gt['layoutHeight'], c)
    vfloor = (-vfloor / np.pi + 0.5) * args.img_height
    vceil = (-vceil / np.pi + 0.5) * args.img_height

    cor_x = np.repeat(u, 2)
    cor_y = np.stack([vceil, vfloor], -1).reshape(-1)
    cor_xy = np.stack([cor_x, cor_y], -1)

    with open(txt_path, 'w') as fo:
        for x, y in cor_xy:
            fo.write(f'{x:.2f} {y:.2f}\n')

def make_split(dataset, split, args):
    with open(dataset) as fi:
        file_ids = ['_'.join(l.strip().split()) for l in fi]
    
    for fileid in file_ids:
        json_path = os.path.join(args.ann_root, fileid + '_label.json')
        if os.path.isfile(json_path):
            txt_path = os.path.join(args.out_dir, split, 'label_cor')
            os.makedirs(txt_path, exist_ok=True)
            txt_path = os.path.join(txt_path, fileid + '.txt')
            json2txt(json_path, txt_path, args)
            
            # Here, we assume the root Matterport3D directory is flat,
            # with all file IDs under one parent directory. If your root
            # Matterport3D has a hierarchy, adapt the next two lines to your use case
            srcimg = os.path.join(args.img_root, fileid.split('_')[-1] + '.png')
            dstimg = os.path.join(args.out_dir, split, 'img')
            os.makedirs(dstimg, exist_ok=True)
            dstimg = os.path.join(dstimg, fileid + '.png')
            os.symlink(os.path.abspath(srcimg), os.path.abspath(dstimg))
            

if __name__ == '__main__':
    args = parser.parse_args()
    make_split(args.dataset, args.split_name, args)

