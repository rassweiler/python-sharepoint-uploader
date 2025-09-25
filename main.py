#!/usr/bin/env python3

import os
import platform
import subprocess
import logging
import sys
import tomllib
from datetime import datetime
from typing import Any, Dict, Iterator, List
from pathlib import Path
from SharepointExport import SharepointExport

class NetworkFileSync():
    def __init__(self, setting_file: str = '.setup.toml'):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='./logs/.NetworkFileSync_' + datetime.now().strftime('%Y-%m-%d_%H-%M') + '.log', level=logging.DEBUG)
        self.logger.info('____Started Network Sync____')
        self.settings: Dict[str, Any] = {}
        self.target_devices: List[Dict[str, str]] = []
        self.local_save_folder: str = "./RemoteFiles/"
        self.sharepoint_sites: List[Dict[str, str]] = []
        self.LoadSettings(setting_file)
        self.sharepoint_export: SharepointExport
        self.root_dir = Path(__file__).parent

    def LoadSettings(self, setting_file: str) -> None:
        with open(setting_file, 'rb') as file:
            self.settings: Dict[str, Any] = tomllib.load(file)
            if 'local' in self.settings and 'save_folder' in self.settings['local']:
                self.local_save_folder = self.settings['local']['save_folder']
            else:
                self.logger.warning('Unable to load save folder from settings, using default')
            if 'remote' in self.settings and 'targets' in self.settings['remote']:
                self.target_devices = self.settings['remote']['targets']
            else:
                self.logger.exception('Unable to load remote targets from file %', self.settings)
                raise ValueError('Unable to load remote targets from file %', self.settings)
            if 'sharepoint' in self.settings and 'folders' in self.settings['sharepoint']:
                self.sharepoint_sites = self.settings['sharepoint']['folders']
            else:
                self.logger.exception('Unable to load sharepoint data from file %', self.settings)
                raise ValueError('Unable to load sharepoint data from file %', self.settings)

    def ConnectToSharepoint(self) -> None:
        """
        Attempt to connect using session to a sharepoint site, connection parameters are loaded in from toml file
        :return: bool of connection status
        """
        try:
            self.sharepoint_export = SharepointExport()
        except:
            self.logger.exception('Unable to create sharepoint export')
            raise ValueError('Unable to create sharepoint export')

    def RunRemoteSync(self) -> bool:
        """
        Iterate over all remote devices and call RsyncFromRemote
        :return: None
        """
        for device in self.target_devices:
            result: subprocess.CompletedProcess = self.RsyncFromRemote(device) # pyright: ignore[reportMissingTypeArgument, reportUnknownMemberType, reportUnknownVariableType]
            if not result.returncode == 0:
                self.logger.exception('Error: NetworkFileSync - Unable to sync from remote, return code: %, stoud: %' % (result.returncode, result.stdout)) # pyright: ignore[reportUnknownMemberType]
        return True

    # Run rsync on remote device to copy CSV files over
    def RsyncFromRemote(self, target: Dict[str, str]) -> subprocess.CompletedProcess: # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
        """
        Call Rsync subprocess for targeted device
        :param target: A tuple containing strings [username, ip, path]
        :return: status str
        """
        if platform.system() == 'Linux':
            status: subprocess.CompletedProcess = subprocess.run(args=["rsync", "-ah", target['username'] + "@" + target['ip'] + target['location'], os.path.join(self.local_save_folder)], text=True) # pyright: ignore[reportMissingTypeArgument]
        else:
            status: subprocess.CompletedProcess = subprocess.run(args=["scp", "-r", target['username'] + "@" + target['ip'] + ":" + target['location'] + "*", os.path.join(self.local_save_folder)], text=True) # pyright: ignore[reportMissingTypeArgument]
        '''
        status.args (The arguments used to launch run)
        status.returncode (exit status, 0 is OK)
        status.stdout (If text=True, captured stdout as string or None of nothing was captured)
        status.check_returncode() (Will raise a CalledProcessError is returncode is not 0)
        '''
        return status # pyright: ignore[reportUnknownVariableType] #TODO: setup status feedback

    def UploadFilesToSharepoint(self) -> None:
        """
        Iterate files within local folder and upload them to sharepoint
        :return: None
        """
        for site in self.sharepoint_sites:
            if not site['site_id']:
                return
            if not site['list_id']:
                return
            if not site['remote_path']:
                return
            pathlist: Iterator[Path] = Path(self.local_save_folder + site['sub_folder']).glob('**/*.csv')
            for path in pathlist:
                path_only: str = os.path.join(self.root_dir, path.parent)
                file_name: str = path.name
                try:
                    self.sharepoint_export.upload_file(path_only, file_name, site['site_id'], site['list_id'], site['remote_path'])
                except:
                    self.logger.exception('Unable to upload file:  %s' % os.path.join(path_only, file_name))
                    raise ValueError('Unable to upload file: %s' % os.path.join(path_only, file_name))

if __name__ == "__main__": 
    app = NetworkFileSync()
    # Establish sharepoint session
    app.ConnectToSharepoint()

    # Cycle remote devices and get data
    #is_rsync_ok: bool = app.RunRemoteSync()
    #if not is_rsync_ok:
    #    sys.exit(1)

    # Cycle local files and upload to sharepoint
    app.UploadFilesToSharepoint()
    sys.exit()
    