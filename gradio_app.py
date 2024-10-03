import os
import argparse
import gradio as gr
from PIL import Image
import re

dataset_dir = "dataset"

img_path_list = []
cap_path_list = []

current_index = 0
allow_write = False

load_img_exts = ('.png', '.jpg')
load_cap_exts = ('.txt',)

save_img_ext = '.png'
save_cap_ext = '.txt'

filename_norm_flg = False
fileext_norm_flg = False


def set_load_img_exts(list):
    global load_img_exts
    load_img_exts = tuple(list)
    return load_img_exts


def set_load_cap_exts(list):
    global load_cap_exts
    load_cap_exts = tuple(list)
    return load_cap_exts


def set_save_img_ext(extention):
    global save_img_ext
    save_img_ext = extention
    return save_img_ext


def set_seve_cap_ext(extention):
    global save_cap_ext
    save_cap_ext = extention
    return save_cap_ext


def set_filename_norm_flg(flg):
    global filename_norm_flg
    filename_norm_flg = flg


def set_fileext_norm_flg(flg):
    global fileext_norm_flg
    fileext_norm_flg = flg


# ドロップアウトでフォルダーを見つける


def get_all_folders():
    root_folder = dataset_dir
    folders = []
    for root, dirs, files in os.walk(root_folder):
        for dir_name in dirs:
            folders.append(os.path.join(root, dir_name))
    return folders

# フォルダを読み込んだ時に正規化する


def img_extention_norm(folder_path):
    for path in img_path_list:
        if os.path.splitext(os.path.basename(path))[1] != save_img_ext:
            new_path = os.path.splitext(path)[0] + save_img_ext
            img = Image.open(path)
            try:
                img.save(new_path)
            except OSError:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(new_path)
            os.remove(path)

    img_cap_path_list_reload(folder_path)


def filename_norm(folder_path):

    def rename_file(file_path, new_name):
        if get_basename(file_path) != new_name:
            dir_path = os.path.dirname(file_path)
            extention = os.path.splitext(file_path)[1]
            new_file_path = os.path.join(dir_path, new_name + extention)
            os.rename(file_path, new_file_path)

    if len(img_path_list) == len(cap_path_list):
        for i in range(len(img_path_list)):
            if get_basename(img_path_list[i]) == get_basename(cap_path_list[i]):
                rename_file(img_path_list[i], f"{i:04d}")
                rename_file(cap_path_list[i], f"{i:04d}")

    img_cap_path_list_reload(folder_path)


# 画像ファイルに対応したcaptionファイルを作る（すでにある場合はrename)


def create_missing_captions(folder_path):
    # captionのbasenameリストを作成
    caption_basenames = {os.path.splitext(os.path.basename(path))[
        0] for path in cap_path_list}

    for image_path in img_path_list:
        image_basename = os.path.splitext(os.path.basename(image_path))[0]

        # 画像に対応するcaptionファイルが存在しない場合
        if image_basename not in caption_basenames:
            # 新しいcaptionファイルのパスを作成
            new_caption_path = os.path.join(
                folder_path, f"{image_basename}{save_cap_ext}")

            # 空のcaptionファイルを作成
            with open(new_caption_path, 'w') as f:
                f.write("")

    img_cap_path_list_reload(folder_path)


def img_cap_path_list_reload(folder_path):
    global img_path_list, cap_path_list
    img_path_list = []
    cap_path_list = []
    # フォルダ内の画像ファイルのパスをリストアップ
    img_path_list = [os.path.join(folder_path, f) for f in os.listdir(
        folder_path) if f.endswith(load_img_exts)]
    # フォルダ内のcaptionファイルのパスをリストアップ
    cap_path_list = [os.path.join(folder_path, f) for f in os.listdir(
        folder_path) if f.endswith(load_cap_exts)]

    img_path_list.sort()
    cap_path_list.sort()

# ギャラリーに画像を表示


def images_display(folder_path):
    global img_path_list, cap_path_list, current_index, allow_write
    # 初期化
    # folder_pathのimg,capをリストに格納してソート
    img_cap_path_list_reload(folder_path)

    # ペアのないキャプションファイルを作成
    create_missing_captions(folder_path)

    # file nameとcaptionに渡す空の文字列
    empty_str = ""

    # 画像の拡張子を正規化
    if fileext_norm_flg:
        img_extention_norm(folder_path)

    # ファイルネームを正規化
    if filename_norm_flg:
        filename_norm(folder_path)

    current_index = 0
    allow_write = False
    # バラバラになることがあるのでソート
    img_path_list.sort()
    cap_path_list.sort()

    return [Image.open(img_path) for img_path in img_path_list], empty_str, empty_str


def get_current_file_name():
    global current_index, img_path_list
    file_name = os.path.basename(img_path_list[current_index])
    return file_name


def format_comma_string(input_str):
    input_str = re.sub(r',+', ',', input_str)  # 2つ以上のカンマを1つのカンマに変換
    input_str = re.sub(r'\s+', ' ', input_str)  # 2つ以上の空白を1つの空白に変換
    input_str = re.sub(r',\s*', ', ', input_str)  # カンマの後に必ず1つの空白を追加（余分な空白も除去）
    input_str = input_str.strip()  # 前後の余分な空白を削除

    return input_str

# cappathlist[index]にあるcaptionファイルにcontentを書き込む


def write_caption(content):
    global current_index
    if content != "":
        index = current_index
        path = cap_path_list[index]
        content = format_comma_string(content)
        with open(path, 'w') as cap_file:
            cap_file.write(content)


# cappathlist[index]にあるcaptionファイルを読む


def read_caption():
    global current_index
    index = current_index
    path = cap_path_list[index]
    with open(path, 'r') as cap_file:
        content = cap_file.read()
        content = format_comma_string(content)
    return content


# captionファイルの中の前か後(position)にcaptionを追加する


def add_caption(add_caption, position):
    global current_index
    for cap_path in cap_path_list:
        with open(cap_path, 'r') as cap_file:
            content = cap_file.read()
        with open(cap_path, 'w') as cap_file:
            if position == "prefix":
                # 前置
                caption = add_caption + content
            else:
                # 後置
                caption = content + add_caption
            cap_file.write(caption)

    return read_caption()

# captionの中にある[remove_caption]を削除する


def remove_caption(remove_caption):
    global current_index
    for cap_path in cap_path_list:
        with open(cap_path, 'r') as cap_file:
            content = cap_file.read()
        with open(cap_path, 'w') as cap_file:
            caption = content.replace(remove_caption, '')
            cap_file.write(caption)
    return read_caption()

#


def get_basename(file_path):
    # ファイル名を取得
    file_name = os.path.basename(file_path)
    # 拡張子を取り除いたベースネームを取得
    base_name, _ = os.path.splitext(file_name)
    return base_name


with gr.Blocks() as iface:
    folder = get_all_folders()
    gr.Markdown("# Simple Caption Editor")
    # レイアウト
    with gr.Tab("Editor"):
        with gr.Row():
            with gr.Column():
                folder = gr.Dropdown(choices=folder, label="Folder")
                gallery = gr.Gallery(label="image", columns=5,
                                     show_download_button=False)

            with gr.Column():
                file_name_disply = gr.Textbox(
                    label="File Name", interactive=False)
                caption_display = gr.Textbox(
                    label="Caption", lines=10, interactive=True)

                with gr.Accordion("All Caption Edit", open=False):
                    with gr.Row():
                        custom_caption = gr.Textbox(
                            label="Insert / Remove Caption", lines=5, interactive=True)
                        with gr.Column(scale=1):
                            radio = gr.Radio(["prefix", "postfix"],
                                             label="insert position", value="prefix")
                            insert_btn = gr.Button("Insert")
                            remove_caption_btn = gr.Button("Remove")

    # 設定tab
    with gr.Tab("Settings"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("Normalize filenames (e.g., 0001.png, 0001.txt)")
                filename_norm_cb = gr.Checkbox(
                    label="Enable", value=filename_norm_flg)
                gr.Markdown("Convert and unify extensions")
                with gr.Group():
                    with gr.Column() and gr.Row():
                        fileext_norm_cb = gr.Checkbox(
                            label="Enable", value=fileext_norm_flg)
                        with gr.Group():
                            save_img_ext_tb = gr.Textbox(
                                label="IMAGE : Extension to convert (e.g., .png, .jpg)", value=save_img_ext, interactive=True)
                            save_cap_ext_tb = gr.Textbox(
                                label="CAPTION : Extension to convert (e.g., .txt)", value=save_cap_ext, interactive=True)

            with gr.Column():
                gr.Markdown("Extensions allowed to be read")
                load_img_ext_cb = gr.CheckboxGroup(
                    [".jpg", ".png", ".tif", ".bmp"], label="Image extention",  value=list(load_img_exts))

                load_cap_ext_cb = gr.CheckboxGroup(
                    [".txt", ".caption"], label="Caption extention",  value=list(load_cap_exts))

    # レイアウト終了

    def write_read_caption(content, evt: gr.EventData):
        global current_index, the_first
        # まず書き込む
        if the_first is True:
            # 最初は書き込まない
            the_first = False
        else:
            write_caption(content)
        # 次に読み込む
        try:
            current_index = int(evt._data['index'])
        except Exception:
            pass

        return read_caption(), str(os.path.basename(img_path_list[current_index]))

    def temp_read_caption(evt: gr.EventData):
        global current_index, allow_write
        print(current_index)
        # filename,caption
        allow_write = True
        try:
            current_index = int(evt._data['index'])
        except Exception:
            pass
        return get_current_file_name(), read_caption()

    # ドロップダウンの変化で画像を表示
    folder.change(
        images_display, inputs=folder, outputs=[
            gallery, file_name_disply, caption_display]
    )
    # ギャラリーの遷移でテキストを表示、保存
    gallery.select(
        temp_read_caption, outputs=[file_name_disply, caption_display]
    )

    caption_display.change(
        write_caption, inputs=[caption_display]
    )

    insert_btn.click(
        add_caption, inputs=[custom_caption, radio], outputs=caption_display
    )

    remove_caption_btn.click(
        remove_caption, inputs=custom_caption, outputs=caption_display
    )

    load_img_ext_cb.change(
        set_load_img_exts, inputs=load_img_ext_cb)

    load_cap_ext_cb.change(
        set_load_cap_exts, inputs=load_cap_ext_cb)

    save_img_ext_tb.change(
        set_save_img_ext, inputs=save_img_ext_tb)

    filename_norm_cb.change(set_filename_norm_flg, inputs=filename_norm_cb)

    fileext_norm_cb.change(set_fileext_norm_flg, inputs=fileext_norm_cb)


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen', type=str, default=None,
                        help="Set the server name (e.g., 0.0.0.0)")
    parser.add_argument('--autolaunch', type=bool,
                        default=False, help="auto launch webui")

    return parser


if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    if args.listen:
        iface.launch(server_name=args.listen, inbrowser=args.autolaunch)
    else:
        iface.launch(inbrowser=args.autolaunch)
