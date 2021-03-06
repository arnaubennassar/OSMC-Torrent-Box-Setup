#!/usr/bin python
import pwd
import grp
import os
import sys
import shutil
import subprocess
from tempfile import mkstemp
from uuid import UUID
import re
import MySQLdb
import netifaces as ni

unrar_pkg = 'unrar_5.2.6-1_armhf.deb'
unrar_url = 'http://sourceforge.net/projects/bananapi/files/' + unrar_pkg

sr_repo = 'https://github.com/SickChill/SickChill.git'
sr_path = '/opt/sickrage'
sr_service_content = """[Unit]
Description=Sickrage daemon

[Service]
ExecStart=/usr/bin/python /opt/sickrage/SickBeard.py
Restart=always

[Install]
WantedBy=default.target
"""

cp_repo = 'http://github.com/RuudBurger/CouchPotatoServer'
cp_path = '/opt/CouchPotato'
cp_service_content = """[Unit]
Description=CouchPotato daemon

[Service]
ExecStart=/usr/bin/python /opt/CouchPotato/CouchPotato.py
Restart=always

[Install]
WantedBy=default.target
"""

advancedsettings_base = """<advancedsettings>
	<videodatabase>
		<type>mysql</type>
		<host>{}</host>
		<port>3306</port>
		<user>kodi</user>
		<pass>kodi</pass>
	</videodatabase>
	<videolibrary>
		<importwatchedstate>true</importwatchedstate>
		<importresumepoint>true</importresumepoint>
	</videolibrary>
</advancedsettings>
"""

def main():

	tr_usr = "osmc"
	tr_pwd = "osmc"
	download_dir = "/home/osmc/Downloads"
	incomplete_dir = "/home/osmc/Incomplete"
	media_dir_base = "/mnt/"
	media_dir = "media"
	spotify_name = 'NNSS'

	# if not root...kick out
	if not os.geteuid()==0:
		sys.exit("\nYou must be root to run this application, please use sudo and try again.\n")

	mount_drive = raw_input("Do you want to mount an external drive (Y/N)? ")
	if mount_drive.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
		mount_label = raw_input("Enter directory name (default is media): ")
		if len(mount_label.strip()) > 0:
			media_dir = mount_label.replace("/","")
		proceed = raw_input("Please connect your external drive and then press enter")
		p = subprocess.Popen(['sudo','blkid'])
		p.wait()
		if p.returncode == 0:
			uuid = raw_input("Enter the UUID of your external drive: ")
			if len(uuid.replace("\"","").strip()) == 36:
				#TODO: check format type automatically
				format = raw_input("Enter your disk format type (ext3, ext4, vfat, ntfs): ")
				format.strip()
				media_path = media_dir_base + media_dir
				create_dir(media_path)
				uuid_mount = 'UUID=' + uuid + '  ' + media_path + '  ' + format + '  defaults,noatime  0  0'
				confirm = raw_input("This line will be added in /etc/fstab: '" + uuid_mount + "' - Confirm? (Y/N): ")
				if confirm in ['y', 'Y', 'yes', 'Yes', 'YES']:
					with open('/etc/fstab', 'a') as fstab:
						fstab.write(uuid_mount)
						fstab.close()
					p = subprocess.Popen(['sudo','mount','-a'])
					p.wait()
					if p.returncode == 0:
						p = subprocess.Popen(['sudo','blkid'])
						p.wait()
						if p.returncode == 0:
							print 'Drive mounted!'
							print '---------------------'
					os.system("mkdir "+media_path+"/DOWNLOADS")
					os.system("mkdir "+media_path+"/incomplete_downloads")
				else: print 'Mounting aborted.'
			else: print 'Error: UUID provided is not valid. Mounting aborted.'

	install_transmission = raw_input("Do you want to install Transmission (Y/N) ? ")
	install_sickrage = raw_input("Do you want to install SickRage (Y/N) ? ")
	install_couchpotato = raw_input("Do you want to install CouchPotato (Y/N) ? ")
	install_mysql = raw_input("Do you want to install MySql (Y/N) ? ")
	install_spotify = raw_input("Do you want to install SPOTIFY (Y/N) ? ")
	install_plex = raw_input("Do you want to install PLEX (Y/N) ? ")
	install_pi_hole = raw_input("Do you want to install PI-HOLE (Y/N) ? ")
	change_password = raw_input("Do you want to change password after instalations (Y/N) ? ")

	p = subprocess.Popen(['sudo', 'apt-get', 'update'])
	p.wait()
	if p.returncode == 0:
		if install_transmission.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			tr_usr_input = raw_input("Enter Transmission username (Default: 'osmc') : ")
			tr_pwd_input = raw_input("Enter Transmission password (Default: 'osmc') : ")
			download_dir = media_path+"/DOWNLOADS"
			incomplete_dir = media_path+"/incomplete_downloads"
			# download_dir_input = raw_input("Enter download dir absolute path (Default: /home/osmc/Downloads): ")
			# incomplete_dir_input = raw_input("Enter incomplete dir absolute path (Default: /home/osmc/Incomplete): ")

			if len(tr_usr_input.strip()) > 1:
				tr_usr = tr_usr_input
			if len(tr_pwd_input.strip()) > 1:
				tr_pwd = tr_pwd_input
			# if len(download_dir_input.strip()) > 1:
			# 	download_dir = download_dir_input
			# if len(incomplete_dir_input.strip()) > 1:
			# 	incomplete_dir = incomplete_dir_input

			if do_transmission(tr_usr, tr_pwd, download_dir, incomplete_dir):
				print 'Transmission installed!'
		if install_spotify.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			spotify_name_input = raw_input("Enter Spotify device name (Default: 'NNSS') : ")

			if len(spotify_name_input.strip()) > 1:
				spotify_name = spotify_name_input

			if do_spotify(spotify_name):
				# print bg.blue + 'Spotify installed!' + bg.rs
				print 'Spotify installed!'
		if install_plex.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			if do_plex():
				# print bg.blue + 'Plex installed!' + bg.rs
				print 'PLEX installed!'
		if install_pi_hole.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			if do_pi_hole():
				# print bg.blue + 'PI-HOLE installed!' + bg.rs
				print 'pi-hole installed!'
		if install_sickrage.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			if do_sickrage(unrar_url, unrar_pkg, sr_repo, sr_path):
				# print bg.blue + 'Sick SickRage installed!' + bg.rs
				print 'SickRage installed!'
		if install_couchpotato.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			if do_couchpotato(cp_repo, cp_path):
				# print bg.blue + 'Couch Potato installed!' + bg.rs
				print 'CouchPotato installed!'
		if install_mysql.strip() in ['y', 'Y', 'yes', 'Yes', 'YES']:
			if do_mysql():
				print 'MySql installed!'
			else: print 'Error during MySql configuration'
		if change_password in ['y', 'Y', 'yes', 'Yes', 'YES']:
			os.system("passwd")
		print 'Installation complete!'

def create_dir(path):
	if not os.path.exists(path):
		os.makedirs(path)
	elif not os.access(os.path.dirname(path), os.W_OK):
		sys.exit("Error: unable to create directory " + path);

def chown_dir(path, user, group):
	if not os.path.exists(path):
		sys.exit("Error: file not found. Unable to chmod " + path)
	else:
		uid = pwd.getpwnam(user).pw_uid
		gid = grp.getgrnam(group).gr_gid
		os.chown(path, uid, gid)

def chmod_dir(path, permissions):
	if not os.path.exists(path):
		sys.exit("Error: file not found. Unable to chown " + path)
	else:
		os.chmod(path, permissions)

#TODO: use only one replace method with regex
def replace(file_path, pattern, subst):
	fh, abs_path = mkstemp()
	with open(abs_path, 'w') as new_file:
		with open(file_path) as old_file:
			for line in old_file:
				new_file.write(line.replace(pattern, subst))
	os.close(fh)
	os.remove(file_path)
	shutil.move(abs_path, file_path)

def replace_regex(file_path, pattern, subst):
	regex = re.compile(pattern, re.IGNORECASE)
	fh, abs_path = mkstemp()
	with open(abs_path, 'w') as new_file:
		with open(file_path) as old_file:
			for line in old_file:
				new_file.write(regex.sub(subst, line))
	os.close(fh)
	os.remove(file_path)
	shutil.move(abs_path, file_path)

def validate_path(path):
	norm_path = os.path.normpath(path)
	return os.path.isabs(norm_path)

'''
def get_fs_type(mypath):
	root_type = ""
	for part in psutil.disk_partitions():
		if part.mountpoint == '/':
			root_type = part.fstype
			continue

		if mypath.startswith(part.mountpoint):
			return part.fstype
	return root_type
'''

def do_transmission(username, password, download, incomplete):
	if os.system("transmission-daemon -V") == 0:
		print("TRANSMISSION ALREADY INSTALLED.")
		return ''
	print("FIRST LETS INSTALL TRANSMISSION")
	os.system("sudo apt-get install transmission-daemon -y")
	os.system("sudo chmod g+rw "+download)
	os.system("sudo chgrp -R osmc "+download)
	os.system("sudo chmod g+rw "+incomplete)
	os.system("sudo chgrp -R osmc "+incomplete)
	os.system("sudo usermod -a -G osmc debian-transmission")
	os.system("sudo /etc/init.d/transmission-daemon start")
	os.system("sudo /etc/init.d/transmission-daemon stop")
	config_file = """{
	\"alt-speed-down\": 50,
	\"alt-speed-enabled\": false,
	\"alt-speed-time-begin\": 540,
	\"alt-speed-time-day\": 127,
	\"alt-speed-time-enabled\": false,
	\"alt-speed-time-end\": 1020,
	\"alt-speed-up\": 50,
	\"bind-address-ipv4\": \"0.0.0.0\",
	\"bind-address-ipv6\": \"::\",
	\"blocklist-enabled\": false,
	\"blocklist-url\": \"http://www.example.com/blocklist\",
	\"cache-size-mb\": 10,
	\"dht-enabled\": true,
	\"download-dir\": \""""+download+"""\",
	\"download-limit\": 100,
	\"download-limit-enabled\": 0,
	\"download-queue-enabled\": true,
	\"download-queue-size\": 5,
	\"encryption\": 1,
	\"idle-seeding-limit\": 30,
	\"idle-seeding-limit-enabled\": false,
	\"incomplete-dir\": \""""+incomplete+"""\",
	\"incomplete-dir-enabled\": true,
	\"lpd-enabled\": false,
	\"max-peers-global\": 200,
	\"message-level\": 1,
	\"peer-congestion-algorithm\": \"\",
	\"peer-id-ttl-hours\": 6,
	\"peer-limit-global\": 200,
	\"peer-limit-per-torrent\": 50,
	\"peer-port\": 51413,
	\"peer-port-random-high\": 65535,
	\"peer-port-random-low\": 49152,
	\"peer-port-random-on-start\": false,
	\"peer-socket-tos\": \"default\",
	\"pex-enabled\": true,
	\"port-forwarding-enabled\": false,
	\"preallocation\": 2,
	\"prefetch-enabled\": true,
	\"queue-stalled-enabled\": true,
	\"queue-stalled-minutes\": 30,
	\"ratio-limit\": 2,
	\"ratio-limit-enabled\": false,
	\"rename-partial-files\": true,
	\"rpc-authentication-required\": true,
	\"rpc-bind-address\": \"0.0.0.0\",
	\"rpc-enabled\": true,
	\"rpc-host-whitelist\": \"\",
	\"rpc-host-whitelist-enabled\": true,
	\"rpc-password\": \""""+username+"""\",
	\"rpc-port\": 9091,
	\"rpc-url\": \"/transmission/\",
	\"rpc-username\": \""""+password+"""\",
	\"rpc-whitelist\": \"*.*.*.*\",
	\"rpc-whitelist-enabled\": true,
	\"scrape-paused-torrents-enabled\": true,
	\"script-torrent-done-enabled\": false,
	\"script-torrent-done-filename\": \"\",
	\"seed-queue-enabled\": false,
	\"seed-queue-size\": 10,
	\"speed-limit-down\": 100,
	\"speed-limit-down-enabled\": false,
	\"speed-limit-up\": 100,
	\"speed-limit-up-enabled\": false,
	\"start-added-torrents\": true,
	\"trash-original-torrent-files\": false,
	\"umask\": 2,
	\"upload-limit\": 100,
	\"upload-limit-enabled\": 0,
	\"upload-slots-per-torrent\": 14,
	\"utp-enabled\": true
	}"""
	with open("tmp_settings.json", 'w+') as new_file:
		new_file.write(config_file)
	os.system("sudo mv tmp_settings.json /etc/transmission-daemon/settings.json")
	os.system("sudo /etc/init.d/transmission-daemon start")


	return True

def do_plex():
	os.system("sudo apt-get install apt-transport-https -y --force-yes")
	os.system("wget -O - https://dev2day.de/pms/dev2day-pms.gpg.key | sudo apt-key add -")
	os.system('echo "deb https://dev2day.de/pms/ stretch main" | sudo tee /etc/apt/sources.list.d/pms.list')
	os.system("sudo apt-get update")
	os.system("sudo apt-get install -t stretch plexmediaserver-installer -y")
	return True

def do_pi_hole():
	os.system("sudo apt-get install whiptail")
	os.system("sudo apt-get install iproute2")
	os.system("sudo curl -sSL https://install.pi-hole.net | sudo bash")
	return True

def do_spotify(spotify_name):
	if os.system("sudo systemctl status raspotify") == 0:
	    print("SPOTIFY ALREADY INSTALLED.")
	    return ''
	os.system("sudo apt-get -y install apt-transport-https")
	os.system("curl -sSL https://dtcooper.github.io/raspotify/key.asc | sudo apt-key add -v -")
	os.system("echo 'deb https://dtcooper.github.io/raspotify jessie main' | sudo tee /etc/apt/sources.list.d/raspotify.list")
	os.system("sudo apt-get update")
	os.system("sudo apt-get install apt-transport-https")
	os.system("sudo apt-get -y install raspotify")
	spotify_config = """DEVICE_NAME="""+spotify_name+"""
	BITRATE="320"
	#"""
	with open("tmp_raspotify", 'w+') as new_file:
	    new_file.write(spotify_config)
	os.system("sudo mv tmp_raspotify /etc/default/raspotify")
	os.system("sudo systemctl restart raspotify")
	with open("tmp_raspotify_kodi", 'w+') as new_file:
	    new_file.write("raspotify\\raspotify.service")
	os.system("sudo mv tmp_raspotify_kodi /etc/osmc/apps.d/spotify-connect")
	return True

def do_sickrage(unrar_url, unrar_pkg, sr_repo, sr_path):
	p = subprocess.Popen(['sudo', 'apt-get', 'install', 'python-cheetah', 'git-core', '-y'])
	p.wait()
	if p.returncode == 0:
		p = subprocess.Popen(['wget', unrar_url])
		p.wait()
		if p.returncode == 0:
			p = subprocess.Popen(['sudo', 'dpkg', '-i', unrar_pkg])
			p.wait()
			if p.returncode == 0:
				p = subprocess.Popen(['sudo', 'rm', unrar_pkg])
				p.wait()
				if p.returncode == 0:
					p = subprocess.Popen(['sudo', 'git', 'clone', sr_repo, sr_path])
					p.wait()
					if p.returncode == 0:
						p = subprocess.Popen(['sudo', 'chown', '-R', 'osmc:osmc', sr_path])
						p.wait()
						if p.returncode == 0:
							sr_service = 'sickrage.service'
							with open(sr_service, 'w') as fout:
								fout.write(sr_service_content)
								fout.close()
							p = subprocess.Popen(['sudo', 'mv', sr_service, '/etc/systemd/system/' + sr_service])
							p.wait()
							if p.returncode == 0:
								p = subprocess.Popen(['sudo', 'systemctl', 'daemon-reload'])
								p.wait()
								if p.returncode == 0:
									p = subprocess.Popen(['sudo', 'systemctl', 'start', sr_service])
									p.wait()
									if p.returncode == 0:
										p = subprocess.Popen(['sudo', 'systemctl', 'enable', sr_service])
										p.wait()
										if p.returncode == 0:
											return True
										else: sys.exit('Error: unable to enable sickrage at startup')
									else: sys.exit('Error: unable to start sickrage service')
								else: sys.exit('Error: unable to reload service')
							else: sys.exit('Error: unable to create sickrage.service')
						else: sys.exit('Error: unable to create sickrage.service')
					else: sys.exit('Error: unable to clone Sickrage repo')
				else: pass
			else: sys.exit('Error: unable to install unrar')
		else: sys.exit('Error: unable to install unrar')
	else: sys.exit('Error: unable to install git-core')

def do_couchpotato(cp_repo, cp_path):
	p = subprocess.Popen(['sudo', 'git', 'clone', cp_repo, cp_path])
	p.wait()
	if p.returncode == 0:
		p = subprocess.Popen(['sudo', 'chown', '-R', 'osmc:osmc', cp_path])
		p.wait()
		if p.returncode == 0:
			cp_service = 'couchpotato.service'
			with open(cp_service, 'w') as fout:
				fout.write(cp_service_content)
				fout.close()
			p = subprocess.Popen(['sudo', 'mv', cp_service, '/etc/systemd/system/' + cp_service])
			p.wait()
			if p.returncode == 0:
				p = subprocess.Popen(['sudo', 'systemctl', 'daemon-reload'])
				p.wait()
				if p.returncode == 0:
					p = subprocess.Popen(['sudo', 'systemctl', 'start', cp_service])
					p.wait()
					if p.returncode == 0:
						p = subprocess.Popen(['sudo', 'systemctl', 'enable', cp_service])
						p.wait()
						if p.returncode == 0:
							return True
						else: sys.exit('Error: unable to enable couchpotato at startup')
					else: sys.exit('Error: unable to start couchpotato service')
				else: sys.exit('Error: unable to reload service')
			else: sys.exit('Error: unable to create couchpotato.service')
		else: sys.exit('Error: unable to create couchpotato.service')
	else: sys.exit('Error: unable to clone CouchPotato repo')

def do_mysql():
	p = subprocess.Popen(['sudo','apt-get','install','mysql-server-5.5','-y'])
	p.wait()
	if p.returncode == 0:
		file_path = '/etc/mysql/my.cnf'
		shutil.copyfile(file_path,file_path + '.orig')
		replace_regex(file_path, 'bind-address', '#bind-address')
		p = subprocess.Popen(['sudo','service','mysql','restart'])
		p.wait()
		if p.returncode == 0:
			print 'MySql service restarted'
			mysql_pwd = raw_input("Enter mysql password for root user: ")
			con = MySQLdb.connect('localhost', 'root', mysql_pwd.replace(" ",""))
			with con:
				cur = con.cursor()
				#cur.execute("CREATE USER 'kodi' IDENTIFIED BY 'kodi'")
				cur.execute("GRANT ALL ON *.* TO 'kodi'")
				ni.ifaddresses('eth0')
				ip = ni.ifaddresses('eth0')[2][0]['addr']
				advancedsettings = advancedsettings_base.format(ip)
				with open('advancedsettings.xml', 'w') as fout:
					fout.write(advancedsettings)
					fout.close()
				p = subprocess.Popen(['sudo', 'mv', 'advancedsettings.xml', '/home/osmc/.kodi/userdata/' + 'advancedsettings.xml'])
				p.wait()
				if p.returncode == 0:
					return True
	return False


if __name__ == "__main__":main()
