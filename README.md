# DICOM 2D/MPR Viewer



CTなどのDICOM画像（Axial）と、それから再構成したMPR断面（Sagittal/Coronal）を同時に表示・操作できるPython製の簡易ビューアです。

## ✨ 主な機能

* Axial, Sagittal, Coronal の3断面表示
* スライス位置のインタラクティブな変更
* Window Width (WW) / Window Level (WL) の調整
* Axial画像上にMPR断面位置をラインで表示

## 🔧 環境構築 (インストール)

このアプリはPythonで動作します。

1.  **Pythonのインストール**
    * [Python公式サイト](https://www.python.org/) からPython (3.8以降を推奨) をインストールしてください。

2.  **リポジトリのクローン**
    ```bash
    git clone [https://github.com/](https://github.com/)[あなたのユーザ名]/[リポジトリ名].git
    cd [リポジトリ名]
    ```

3.  **必要なライブラリのインストール**
    このプロジェクトでは以下のライブラリを使用します。
    
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 使い方

1.  **アプリの起動**
    ```bash
    python dicom_viewer.py
    ```

2.  **フォルダの選択**
    * 起動すると、DICOMファイル（`.dcm`）が格納されているフォルダを選択するダイアログが開きます。

3.  **基本操作**
    * **Windowing (WW/WL):** スライダを動かして、画像の明るさ（WL）とコントラスト（WW）を調整します。
    * **Slices & View:**
        * **Axial:** 原画像（左側）のスライス位置を動かします。
        * **MPR:** 再構成断面（右側）のスライス位置を動かします。
        * **Sagittal/Coronal:** 右側に表示する断面の向きを切り替えます。

## 📸 スクリーンショット

（ここにアプリのスクリーンショット画像を挿入します）

* **Sagittal表示時:**
    

* **Coronal表示時:**
    

## 📝 ライセンス

MIT License

Copyright (c) 2025 Kyushokugorira

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.