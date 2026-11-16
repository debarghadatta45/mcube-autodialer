import os
import pycdlib

def create_dmg():
    output_dmg = os.path.join("portal", "public", "downloads", "MCUBE_AutoDialer.dmg")
    os.makedirs(os.path.dirname(output_dmg), exist_ok=True)

    iso = pycdlib.PyCdlib()
    iso.new(joliet=3, rock_ridge='1.09', vol_ident='MCUBE_DIALER')

    app_root = 'MCUBE_AutoDialer.app'
    iso.add_directory('/APP', joliet_path='/MCUBE_AutoDialer.app', rr_name='MCUBE_AutoDialer.app')
    iso.add_directory('/APP/CONTENTS', joliet_path='/MCUBE_AutoDialer.app/Contents', rr_name='Contents')
    iso.add_directory('/APP/CONTENTS/MACOS', joliet_path='/MCUBE_AutoDialer.app/Contents/MacOS', rr_name='MacOS')

    info_plist = os.path.join(app_root, 'Contents', 'Info.plist')
    if os.path.exists(info_plist):
        iso.add_file(info_plist, '/APP/CONTENTS/INFO.PLI;1', joliet_path='/MCUBE_AutoDialer.app/Contents/Info.plist', rr_name='Info.plist')

    launcher = os.path.join(app_root, 'Contents', 'MacOS', 'MCUBE_AutoDialer')
    if os.path.exists(launcher):
        iso.add_file(launcher, '/APP/CONTENTS/MACOS/LAUNCHER.;1', joliet_path='/MCUBE_AutoDialer.app/Contents/MacOS/MCUBE_AutoDialer', rr_name='MCUBE_AutoDialer')

    pyc = os.path.join(app_root, 'Contents', 'MacOS', 'autodialer.pyc')
    if os.path.exists(pyc):
        iso.add_file(pyc, '/APP/CONTENTS/MACOS/AUTODIAL.PYC;1', joliet_path='/MCUBE_AutoDialer.app/Contents/MacOS/autodialer.pyc', rr_name='autodialer.pyc')

    cfg = 'config.json'
    if os.path.exists(cfg):
        iso.add_file(cfg, '/CONFIG.JSO;1', joliet_path='/config.json', rr_name='config.json')

    iso.write(output_dmg)
    iso.close()
    print(f"[OK] Generated {output_dmg} ({os.path.getsize(output_dmg)} bytes)")

if __name__ == "__main__":
    create_dmg()
