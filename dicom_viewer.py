import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pydicom
import numpy as np
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk # Pillowが必要

"""
DICOM画像ビューア
指定されたフォルダからDICOMシリーズを読み込み、
Axial（原画像）と、SagittalまたはCoronal（再構成断面）を
インタラクティブに表示するアプリです。
"""

class DicomViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DICOM 2D/MPR Viewer")
        self.root.geometry("1000x750")

        # --- データ関連の変数 ---
        self.dicom_files = []
        self.volume_data = None # 3Dボクセルデータ (HU値)
        self.pixel_spacing = (1.0, 1.0)
        self.slice_thickness = 1.0

        # --- GUIコンポーネント ---
        
        # --- メインフレーム ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 上部: 画像表示フレーム ---
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)

        # Matplotlib Figureのセットアップ
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.fig.patch.set_facecolor('#f0f0f0') # Tkinterの背景色に合わせる

        # 1. Axial (原画像)
        self.ax_axial = self.fig.add_subplot(1, 2, 1)
        self.ax_axial.set_title("Axial")
        self.ax_axial.set_aspect('equal')
        self.ax_axial.axis('off')

        # 2. Sagittal / Coronal (再構成断面)
        self.ax_mpr = self.fig.add_subplot(1, 2, 2)
        self.ax_mpr.set_title("Sagittal") # 初期値
        self.ax_mpr.axis('off')

        # Matplotlib CanvasをTkinterに埋め込む
        self.canvas = FigureCanvasTkAgg(self.fig, master=image_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.fig.tight_layout()

        # --- 下部: コントロールフレーム ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        # --- コントロール 1: WW/WL ---
        wwl_frame = ttk.LabelFrame(control_frame, text="Windowing")
        wwl_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # WL (Window Level)
        ttk.Label(wwl_frame, text="WL:").pack(side=tk.LEFT, padx=5)
        self.wl_var = tk.IntVar(value=40)
        self.wl_slider = ttk.Scale(wwl_frame, from_=-1000, to=1000, orient=tk.HORIZONTAL,
                                   variable=self.wl_var, command=self.update_images)
        self.wl_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # WW (Window Width)
        ttk.Label(wwl_frame, text="WW:").pack(side=tk.LEFT, padx=5)
        self.ww_var = tk.IntVar(value=400)
        self.ww_slider = ttk.Scale(wwl_frame, from_=1, to=4000, orient=tk.HORIZONTAL,
                                   variable=self.ww_var, command=self.update_images)
        self.ww_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- コントロール 2: スライス/モード ---
        slice_frame = ttk.LabelFrame(control_frame, text="Slices & View")
        slice_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Axialスライス
        ttk.Label(slice_frame, text="Axial:").pack(side=tk.LEFT, padx=5)
        self.axial_slice_var = tk.IntVar(value=0)
        self.axial_slider = ttk.Scale(slice_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.axial_slice_var, command=self.update_images)
        self.axial_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.axial_label = ttk.Label(slice_frame, text="0/0")
        self.axial_label.pack(side=tk.LEFT, padx=5)

        # MPR (Sagittal/Coronal) スライス
        ttk.Label(slice_frame, text="MPR:").pack(side=tk.LEFT, padx=5)
        self.mpr_slice_var = tk.IntVar(value=0)
        self.mpr_slider = ttk.Scale(slice_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                    variable=self.mpr_slice_var, command=self.update_images)
        self.mpr_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.mpr_label = ttk.Label(slice_frame, text="0/0")
        self.mpr_label.pack(side=tk.LEFT, padx=5)

        # 表示モード (Sagittal / Coronal)
        self.mpr_mode_var = tk.StringVar(value="Sagittal")
        ttk.Radiobutton(slice_frame, text="Sagittal", variable=self.mpr_mode_var,
                        value="Sagittal", command=self.update_view_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(slice_frame, text="Coronal", variable=self.mpr_mode_var,
                        value="Coronal", command=self.update_view_mode).pack(side=tk.LEFT, padx=5)
        
        # --- メニューバー ---
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open DICOM Folder", command=self.load_dicom_folder)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        # --- 初期化 ---
        self.mpr_line = None # Axial上の線
        self.load_dicom_folder() # 起動時にフォルダ選択を促す

    def apply_window(self, image_data, wl, ww):
        """ピクセルデータにWindow Level (WL) と Window Width (WW) を適用する"""
        min_val = wl - (ww / 2)
        max_val = wl + (ww / 2)
        
        # 0-255に正規化
        image_data = np.clip(image_data, min_val, max_val)
        image_data = (image_data - min_val) / ww
        image_data = (image_data * 255.0).astype(np.uint8)
        return image_data

    def load_dicom_folder(self):
        """DICOMフォルダを読み込み、3Dボクセルデータを構築する"""
        folder_path = filedialog.askdirectory(title="Select DICOM Folder")
        if not folder_path:
            if self.volume_data is None:
                messagebox.showerror("Error", "No folder selected. Exiting.")
                self.root.quit()
            return

        try:
            # フォルダ内のDICOMファイルを読み込み
            files = []
            for fname in os.listdir(folder_path):
                fpath = os.path.join(folder_path, fname)
                if os.path.isfile(fpath):
                    try:
                        dcm = pydicom.dcmread(fpath)
                        # CT画像かどうかの簡易チェック (Modality)
                        if 'Modality' in dcm and dcm.Modality == 'CT':
                            files.append(dcm)
                    except Exception:
                        continue # DICOMファイル以外は無視
            
            if not files:
                raise ValueError("No valid CT DICOM files found in the selected folder.")

            # スライス位置 (InstanceNumber または SliceLocation) でソート
            files.sort(key=lambda x: float(x.InstanceNumber))
            
            self.dicom_files = files

            # DICOMタグから情報を取得 (最初のファイルから)
            dcm_template = self.dicom_files[0]
            
            # ピクセルスペーシング (X, Y)
            self.pixel_spacing = (float(dcm_template.PixelSpacing[0]), float(dcm_template.PixelSpacing[1]))
            
            # スライス厚 (Z)
            if 'SliceThickness' in dcm_template:
                self.slice_thickness = float(dcm_template.SliceThickness)
            else:
                # スライス厚がない場合、スライス間隔から推定
                if len(self.dicom_files) > 1:
                    self.slice_thickness = abs(self.dicom_files[1].SliceLocation - self.dicom_files[0].SliceLocation)
                else:
                    self.slice_thickness = self.pixel_spacing[0] # フォールバック

            # デフォルトのWW/WL
            if 'WindowCenter' in dcm_template and 'WindowWidth' in dcm_template:
                # 複数のWW/WLがある場合、最初のを採用
                if isinstance(dcm_template.WindowCenter, pydicom.multival.MultiValue):
                    wl = float(dcm_template.WindowCenter[0])
                    ww = float(dcm_template.WindowWidth[0])
                else:
                    wl = float(dcm_template.WindowCenter)
                    ww = float(dcm_template.WindowWidth)
                
                self.wl_var.set(int(wl))
                self.ww_var.set(int(ww))

            # Rescale Slope / Intercept
            slope = float(dcm_template.RescaleSlope) if 'RescaleSlope' in dcm_template else 1.0
            intercept = float(dcm_template.RescaleIntercept) if 'RescaleIntercept' in dcm_template else 0.0

            # 3Dボクセルデータの構築 (HU値に変換)
            # (Z, Y, X) の形状にする
            shape = (len(self.dicom_files), dcm_template.Rows, dcm_template.Columns)
            self.volume_data = np.zeros(shape, dtype=np.int16)

            for i, dcm in enumerate(self.dicom_files):
                pixel_array = dcm.pixel_array.astype(np.int16)
                # HU値に変換
                hu_image = pixel_array * slope + intercept
                self.volume_data[i] = hu_image
                
            print(f"Loaded {len(self.dicom_files)} slices.")
            print(f"Volume shape (Z, Y, X): {self.volume_data.shape}")
            print(f"Pixel Spacing (X, Y): {self.pixel_spacing}")
            print(f"Slice Thickness (Z): {self.slice_thickness}")

            # スライダの範囲を更新
            self.axial_slider.config(to=self.volume_data.shape[0] - 1)
            self.axial_slice_var.set(self.volume_data.shape[0] // 2)

            self.update_view_mode() # MPRスライダの範囲も更新

        except Exception as e:
            messagebox.showerror("Error loading DICOM", f"An error occurred: {e}")
            self.volume_data = None


    def update_view_mode(self):
        """Sagittal/Coronalの表示モードが切り替わった時に呼び出される"""
        if self.volume_data is None:
            return

        mode = self.mpr_mode_var.get()
        current_mpr_slice = self.mpr_slice_var.get()

        if mode == "Sagittal":
            # (Z, Y, X) -> (Z, X, Y) の軸でスライス (Y軸方向)
            # スライダの範囲は X (volume.shape[2])
            mpr_max = self.volume_data.shape[2] - 1
            self.ax_mpr.set_title("Sagittal")
            
            # アスペクト比 (Z / Y)
            aspect_mpr = self.slice_thickness / self.pixel_spacing[1]
            self.ax_mpr.set_aspect(aspect_mpr)

        else: # Coronal
            # (Z, Y, X) -> (Z, Y, X) の軸でスライス (X軸方向)
            # スライダの範囲は Y (volume.shape[1])
            mpr_max = self.volume_data.shape[1] - 1
            self.ax_mpr.set_title("Coronal")
            
            # アスペクト比 (Z / X)
            aspect_mpr = self.slice_thickness / self.pixel_spacing[0]
            self.ax_mpr.set_aspect(aspect_mpr)

        self.mpr_slider.config(to=mpr_max)
        
        # スライダの位置が範囲外にならないように調整
        if current_mpr_slice > mpr_max:
            self.mpr_slice_var.set(mpr_max // 2)
        elif current_mpr_slice < 0:
             self.mpr_slice_var.set(mpr_max // 2)
        else:
            # 範囲内なら中央付近にリセット (切り替え時はわかりやすいため)
            self.mpr_slice_var.set(mpr_max // 2)

        self.update_images() # 画像を更新


    def update_images(self, *args):
        """スライダの値に基づき、画像表示を更新する"""
        if self.volume_data is None:
            return

        # スライダから現在の値を取得
        wl = self.wl_var.get()
        ww = self.ww_var.get()
        axial_slice_idx = self.axial_slice_var.get()
        mpr_slice_idx = self.mpr_slice_var.get()
        mode = self.mpr_mode_var.get()

        # 1. Axial (原画像) の準備
        # (Z, Y, X) から Z を選択
        axial_image_hu = self.volume_data[axial_slice_idx, :, :]
        axial_image_display = self.apply_window(axial_image_hu, wl, ww)
        
        # 2. MPR (Sagittal/Coronal) の準備
        if mode == "Sagittal":
            # (Z, Y, X) から X を選択 (Sagittal断面)
            # (Z, Y, mpr_slice_idx) を取り出す
            mpr_image_hu = self.volume_data[:, :, mpr_slice_idx]
            mpr_image_display = self.apply_window(mpr_image_hu, wl, ww)

        else: # Coronal
            # (Z, Y, X) から Y を選択 (Coronal断面)
            # (Z, mpr_slice_idx, X) を取り出す
            mpr_image_hu = self.volume_data[:, mpr_slice_idx, :]
            mpr_image_display = self.apply_window(mpr_image_hu, wl, ww)

        # 3. 画像の描画
        # Axial
        self.ax_axial.clear()
        self.ax_axial.imshow(axial_image_display, cmap='gray', aspect='equal') # Axialはピクセルスペーシングが等しい前提
        self.ax_axial.set_title(f"Axial (Z: {axial_slice_idx})")
        self.ax_axial.axis('off')

        # MPR
        self.ax_mpr.clear()
        # アスペクト比を再設定 (clear()でリセットされるため)
        if mode == "Sagittal":
            aspect_mpr = self.slice_thickness / self.pixel_spacing[1]
            self.ax_mpr.set_title(f"Sagittal (X: {mpr_slice_idx})")
        else: # Coronal
            aspect_mpr = self.slice_thickness / self.pixel_spacing[0]
            self.ax_mpr.set_title(f"Coronal (Y: {mpr_slice_idx})")
        
        self.ax_mpr.imshow(mpr_image_display, cmap='gray', aspect=aspect_mpr)
        self.ax_mpr.axis('off')


        # 4. Axial画像上にMPR断面位置の直線を描画
        if mode == "Sagittal":
            # 縦線 (X座標 = mpr_slice_idx)
            self.mpr_line = self.ax_axial.axvline(x=mpr_slice_idx, color='red', linestyle='--')
        else: # Coronal
            # 横線 (Y座標 = mpr_slice_idx)
            self.mpr_line = self.ax_axial.axhline(y=mpr_slice_idx, color='red', linestyle='--')

        # 5. ラベルの更新
        self.axial_label.config(text=f"{axial_slice_idx}/{self.volume_data.shape[0] - 1}")
        if mode == "Sagittal":
            self.mpr_label.config(text=f"{mpr_slice_idx}/{self.volume_data.shape[2] - 1}")
        else:
            self.mpr_label.config(text=f"{mpr_slice_idx}/{self.volume_data.shape[1] - 1}")

        # Canvasの再描画
        self.canvas.draw()


if __name__ == "__main__":
    # 高DPI対応 (Windowsの場合)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = DicomViewerApp(root)
    root.mainloop()