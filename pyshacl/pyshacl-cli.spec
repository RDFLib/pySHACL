# -*- mode: python ; coding: utf-8 -*-
## run `pyinstaller pyshacl-cli.spec` to create `dist/pyshacl.exe` dist
## note it requires pywin32

block_cipher = None

a = Analysis(
            ['cli.py'],
            pathex=['.'],
            binaries=[
                ('assets/shacl.pickle','assets'),
                ('assets/shacl-shacl.pickle','assets')
            ],
            datas=[
                ('assets/shacl.ttl','assets'),
                ('assets/shacl-shacl.ttl','assets')
            ],
            hiddenimports=[
                'rdflib.plugins',
                'rdflib',
                'urllib3',
                'win32com.gen_py',
                'pkg_resources.py2_warn'
            ],
            hookspath=[],
            runtime_hooks=[],
            excludes=[],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False
)

pyz = PYZ(
            a.pure,
            a.zipped_data,
            cipher=block_cipher
)

exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name='pyshacl',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            upx_exclude=[],
            runtime_tmpdir=None,
            console=True
)
