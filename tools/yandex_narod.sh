#!/bin/bash

#denis.obydennykh@gmail.com
#icq 4010808
#skype denis.obydennykh
#script for uploading backups to yandex.disk
#2010

usage()
{
cat << EOF
usage: $0 options source_file_or_dir1 [source_file_or_dir2 [source_file_or_dir3]]

OPTIONS:
   -h      Show this message
   -a      Compress source to archive - possible: tar, tar.gz, tar.bz, zip, 7z, rar. All source directories are compressed with zip by default.
   -l      Login to upload
   -p      Password to upload
   -s      Save archives, don't delete them after upload
   -d      Directory to create (and store if -s) archives, by default used current dir
EOF
}

ARCHIVE=""
LOGIN=glader.dump
PASSWORD=xxxxx
SAVE=1
DIRECTORY=/home/www/backup/daily
SERVICE=yandex_disk

while getopts “ha:l:p:sd” OPTION
do
	case $OPTION in
	h)
        	usage
		exit 1
		;;
	a)
		ARCHIVE=$OPTARG
		;;
	l)
		LOGIN=$OPTARG
		;;
	p)
		PASSWORD=$OPTARG
		;;
	s)
		SAVE=1
		;;
	d)
		DIRECTORY=$OPTARG
		;;
	esac
done
shift $(($OPTIND - 1))

#if [ -e "yandex_narod.cookie.txt" ]; then
	echo "Loggin to yandex..."
	curl -s --cookie-jar yandex_narod.cookie.txt https://passport.yandex.ru/passport?mode=auth -d login=$LOGIN -d passwd=$PASSWORD -d twoweeks=yes
#else
#	echo "Already authorized in yandex"
#fi

token=$(curl -s --cookie-jar yandex_narod.cookie.txt --cookie yandex_narod.cookie.txt http://narod.yandex.ru/disk/getstorage/?rnd=$RANDOM)
upload_url=$(echo $token | sed -e 's/getStorage({ //' | sed -e 's/ });//' | sed -e 's/\"//g' | sed -e 's/url://' | cut -d "," -f 1)
hash=$(echo $token | sed -e 's/getStorage({ //' | sed -e 's/ });//' | sed -e 's/ *\"//g' | sed -e 's/hash://' | cut -d "," -f 2)
purl=$(echo $token | sed -e 's/getStorage({ //' | sed -e 's/ });//' | sed -e 's/ *\"//g' | sed -e 's/purl://' | cut -d "," -f 3)
url=$upload_url"?tid="$hash
purl=$purl"?tid="$hash
#echo $token
#echo $url
#echo $hash
#echo $purl

#echo "^^^^ debug"

#echo $@

i=1
for file in "$@"
do
	if [ -e "$file" ]; then
		echo "$i: processing $file"
		if [ -d "$file" ] || [  -n "$ARCHIVE" ]; then
        	        file_basename=$(basename "$file")
	                file_dir=$(dirname "$file")
			file_archivename=$file_dir"/"$file_basename"_"$(date +%Y.%m.%d_%H.%M.%S)"."$ARCHIVE
			case "$ARCHIVE" in
			"tar")
				tar -cvf "$file_archivename" "$file"
			;;
			"tar.gz")
				tar -cvzf "$file_archivename" "$file"
			;;
			"tar.bz")
				tar -cvjf "$file_archivename" "$file"
			;;
			"7z")
				7z a "$file_archivename" "$file"
			;;
			"rar")
				rar a "$file_archivename" "$file"
			;;
			"zip")
				zip -r "$file_archivename" "$file"
			;;
			"")
				# [ -d "$file" ] == true
				file_archivename=$file_archivename"tar.gz"
				tar -cvzf "$file_archivename".tar.gz "$file"
			;;
			*)
				echo "Wrong archive type - '$ARCHIVE' (possible:tar,tar.gz,tar.bz,zip,rar,7z)"
				exit 0;;
			esac
		else
			file_archivename=$file
		fi

		curl --cookie yandex_narod.cookie.txt  -v -e http://narod.yandex.ru  -F 'file=@'"$file_archivename" $url

		if [ $SAVE -ne 1 ] && [ "$file" != "$file_archivename" ]; then
			echo "removing file $file_archivename"
			rm -f $file_archivename
		fi

	else
		echo "ERROR: file $file not found!"
	fi
	let "i+=1";
done
