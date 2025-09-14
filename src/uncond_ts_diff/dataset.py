# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
import tarfile
from pathlib import Path
from urllib import request

from gluonts.dataset.common import load_datasets
from gluonts.dataset.repository.datasets import get_dataset, get_download_path

# ✅ 注意这里：先 Path(...) 再拼 / "datasets"
default_dataset_path: Path = Path(get_download_path()) / "datasets"
wiki2k_download_link: str = (
    "https://github.com/awslabs/gluonts/raw/b89f203595183340651411a41eeb0ee60570a4d9/datasets/wiki2000_nips.tar.gz"
)

def _load_custom_root(root: Path):
    root = root.expanduser().resolve()

    # ✅ 传目录：如果 metadata.json 在根目录，就传 root；
    #    如果在 metadata/ 下，就传 root/"metadata"
    if (root / "metadata.json").exists():
        meta_dir = root
    elif (root / "metadata" / "metadata.json").exists():
        meta_dir = root / "metadata"
    else:
        raise FileNotFoundError(f"metadata.json not found under: {root}")

    train_dir = root / "train"
    test_dir  = root / "test"
    if not (train_dir / "train.json").exists():
        raise FileNotFoundError(f"missing {train_dir/'train.json'}")
    if not (test_dir / "test.json").exists():
        raise FileNotFoundError(f"missing {test_dir/'test.json'}")

    # ⬇️ 这里把 metadata 参数改成 meta_dir（目录）
    return load_datasets(metadata=meta_dir, train=train_dir, test=test_dir)

def get_gts_dataset(dataset_name: str):
    # 1) ✅ 支持 dataset: custom(/abs/path)
    if dataset_name.startswith("custom(") and dataset_name.endswith(")"):
        root = Path(dataset_name[7:-1])  # 去掉 custom( ... )
        return _load_custom_root(root)

    # 2) 兼容：本地缓存目录存在同名数据集则直接加载
    local_root = default_dataset_path / dataset_name
    if (local_root / "metadata.json").exists() or (local_root / "metadata" / "metadata.json").exists():
        return _load_custom_root(local_root)

    # 3) 专门处理 wiki2000_nips（你原来的逻辑）
    if dataset_name == "wiki2000_nips":
        wiki_dataset_path = default_dataset_path / dataset_name
        wiki_dataset_path.parent.mkdir(parents=True, exist_ok=True)
        if not wiki_dataset_path.exists():
            tar_file_path = wiki_dataset_path.parent / f"{dataset_name}.tar.gz"
            request.urlretrieve(wiki2k_download_link, tar_file_path)
            with tarfile.open(tar_file_path) as tar:
                # 简单的安全解压（防目录穿越）
                def is_within(directory, target):
                    ad, at = os.path.abspath(directory), os.path.abspath(target)
                    return os.path.commonprefix([ad, at]) == ad
                for m in tar.getmembers():
                    if not is_within(str(wiki_dataset_path.parent), os.path.join(str(wiki_dataset_path.parent), m.name)):
                        raise Exception("Unsafe path in tar file.")
                tar.extractall(path=wiki_dataset_path.parent)
            os.remove(tar_file_path)
        return load_datasets(
            metadata=wiki_dataset_path / "metadata",
            train=wiki_dataset_path / "train",
            test=wiki_dataset_path / "test",
        )

    # 4) 其余情况回退到官方内置数据集
    return get_dataset(dataset_name)
