import tkinter
from swordfish_launcher.downloader.modpack import AbstractModpack


class ScrollableFrame(tkinter.Frame):
    def __init__(self, parent, *args, scrollbar_side='left', **kw):
        super().__init__(parent, *args, **kw)
        self.scrollbar = tkinter.Scrollbar(parent)
        canvas = tkinter.Canvas(self, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=canvas.yview)
        self.scrollable_region = tkinter.Frame(canvas)
        canvas.create_window(0, 0, window=self.scrollable_region)
        self.scrollable_region.bind('<Configure>', lambda evt: canvas.configure(scrollregion=canvas.bbox('all')))
        self.scrollbar.pack(side=scrollbar_side, fill='y')
        canvas.pack(expand=True, fill='both')


# if __name__=='__main__':
#     root=tkinter.Tk()
#     scf=ScrollableFrame(root, scrollbar_side='right')
#     scf.pack(expand=True,fill='both')
#     import pkgutil
#     image = tkinter.PhotoImage(master=root, data=pkgutil.get_data('swordfish_launcher.gui', 'sunflower.gif'))
#     for _ in range(20):
#         tkinter.Label(scf.scrollable_region, image=image).pack()
#     root.mainloop()
#

OPTIONHEIGHT = 120
IMAGEWIDTH = 120
OPTIIONWIDTH = 500


class ModList(ScrollableFrame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.packs = []

    def add_pack(self, modpack: AbstractModpack):
        modpack_frame = tkinter.Frame(self.scrollable_region,
                                      background='white' if len(self.packs) % 2 == 0 else 'grey')
        modpack_frame.modpack = modpack
        image = modpack._getimage('icon')
        if image:
            max_dimensions = (image.width * OPTIONHEIGHT // image.height, OPTIONHEIGHT)
            if max_dimensions[0] < IMAGEWIDTH:
                image = image.resize(max_dimensions)
            else:
                image = image.resize((IMAGEWIDTH, image.height * IMAGEWIDTH // image.width))
            from PIL import ImageTk
            photoimage = ImageTk.PhotoImage(image, master=modpack_frame)
            modpack_frame.icon = photoimage
            tkinter.Label(modpack_frame, image=photoimage).grid(row=0, column=0, rowspan=3, sticky='w')
        tkinter.Label(modpack_frame, text=modpack.title, font=('', 12, 'bold')).grid(column=1, row=0, sticky='w')
        tkinter.Label(modpack_frame, text=modpack.summary).grid(column=1, row=1, sticky='w')
        self.packs.append(modpack_frame)
        modpack_frame.pack(fill='x', expand=True)


if __name__ == '__main__':
    root = tkinter.Tk()
    modlist = ModList(root)
    modlist.pack(expand=True, fill='both')
    from swordfish_launcher.downloader.third_party.curse import CurseModpack

    for pack in CurseModpack.search('world'):
        print('loading', pack.title)
        modlist.add_pack(pack)
    print('done loading')
    root.mainloop()
