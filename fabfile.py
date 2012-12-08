# -*- coding: utf-8 -*-

import boto
import time
from datetime import date

from fabric.api import *
from fabric.contrib.files import exists, sed, append, upload_template, uncomment

from fab_settings import *

env.ami = 'ami-8f03ede6'
env.directory = '/home/%s/projects/d306' % SSH_USER
env.manage_dir = env.directory + '/src'
env.activate = 'source %s/ENV/bin/activate' % env.directory
env.www_ssh_key = 'ssh-dss AAAAB3NzaC1kc3MAAACAbN+8KDO1jkRluNqiqO2KjkaSn4Qs66zBcV+JaUFrnoVt5tBaEMGW56ihtd1zmPqSufpDKTMXKneZWLAx8evFobvU5S32OKtFpR6oylZwIWg0SQNtjBE7lFHC5VnN4BtjpLp6DBzUOt6mTXYyCjaYhorMWmyw5641KXOsW0V7et0AAAAVALlYgGve+sIVrw7MTQFD4Hvb1utVAAAAgAGktSDpYw1sEC9tA593z3Ymk9r4J939DsKiL3d+RK/RXfY9KgoFtMHmCzL8goYpyWdaE2XQzCrIfp3EFW41NUWUfxsaDzXSEg4Q/CYAfJm7nNDpwv1eAq3c0Mw7RMGEw3pxsAnQrq0snHI7cVhdZ12Z6wO147+ybAbOXW7XF04sAAAAgGzFeuezmdfyS0N4VE42/kgC4SusMTxYOj5nrb8VRvzQ08Msa5FChXIWv0Fj5hMpOVX/gc4uEkbt7knpjqouo+K+8jadQ4I+sRidqG13U6b2UGJy844THSqL3HIhuPmhvWPOFjJbsNFxcoakSqLxn3ewkDzco7CH/aYo9u9VrLwk dsa-key-20080514'
if not env.hosts:
    env.hosts = ['ec2-107-21-102-210.compute-1.amazonaws.com']


def virtualenv(command):
    with cd(env.directory):
        run(env.activate + ' && ' + command)


def _create_server():
    """Creates EC2 Instance"""
    print "Creating instance"
    conn = boto.connect_ec2(EC2_KEY, EC2_SECRET)
    image = conn.get_all_images([env.ami])

    reservation = image[0].run(1, 1, 'ec2_django_micro', ['default'],
        instance_type='t1.micro')

    instance = reservation.instances[0]
    conn.create_tags([instance.id], {"Name": "d306.ru auto"})

    while instance.state == u'pending':
        print "Instance state: %s" % instance.state
        time.sleep(10)
        instance.update()

    print "Instance state: %s" % instance.state
    print "Public dns: %s" % instance.public_dns_name

    return instance.public_dns_name


def create():
    dns = _create_server()
    with settings(hosts=[dns]):
        init()
        production()


def init():
    with settings(user='ubuntu'):
        sudo('apt-get update')
        sudo('apt-get install -y mc nginx mysql-client git-core python-setuptools python-dev runit rrdtool sendmail memcached libjpeg62-dev')
        sudo('apt-get build-dep -y python-mysqldb')

        if not exists('/home/%s' % SSH_USER):
            sudo('yes | adduser --disabled-password %s' % SSH_USER)
            sudo('mkdir /home/%s/.ssh' % SSH_USER)
            sudo('echo "%s" >> /home/%s/.ssh/authorized_keys' % (env.www_ssh_key, SSH_USER))

        append('/etc/sudoers', '%s  ALL=(ALL) NOPASSWD:/usr/bin/sv' % SSH_USER, use_sudo=True)

        if not exists('/var/log/projects/d306'):
            sudo('mkdir -p /var/log/projects/d306')
            sudo('chmod 777 /var/log/projects/d306')

        if exists('/etc/nginx/sites-enabled/default'):
            sudo('rm /etc/nginx/sites-enabled/default')

        if not exists('/etc/nginx/listen'):
            put('tools/nginx/listen', '/etc/nginx/listen', use_sudo=True)
        if not exists('/etc/nginx/fastcgi_params_extended'):
            put('tools/nginx/fastcgi_params_extended', '/etc/nginx/fastcgi_params_extended', use_sudo=True)

        if not exists('/etc/nginx/sites-available/90-d306.conf'):
            sudo('touch /etc/nginx/sites-available/90-d306.conf')
        if not exists('/etc/nginx/sites-enabled/90-d306.conf'):
            sudo('ln -s /etc/nginx/sites-available/90-d306.conf /etc/nginx/sites-enabled/90-d306.conf', shell=False)

        if not exists('/etc/sv/d306'):
            sudo('mkdir -p /etc/sv/d306/supervise')
            sudo('touch /etc/sv/d306/run')
            sudo('chmod 755 /etc/sv/d306/run')
            sudo('ln -s /etc/sv/d306 /etc/service/d306', shell=False)

        sudo('mkdir -p /home/%s/projects/d306' % SSH_USER)
        sudo('chown -R %(user)s:%(user)s /home/%(user)s' % {'user': SSH_USER})


def production():
    upload()
    environment()
    local_settings()
    nginx()
    runit()
    dump()
    migrate()
    restart()


def upload():
    with settings(user=SSH_USER):
        local('git archive -o archive.tar.gz HEAD')
        put('archive.tar.gz', env.directory + '/archive.tar.gz')
        with cd(env.directory):
            run('tar -zxf archive.tar.gz')
            run('rm archive.tar.gz')
        local('del archive.tar.gz')


def environment():
    with settings(user=SSH_USER):
        with cd(env.directory):
            with settings(warn_only=True):
                run('python virtualenv.py ENV')
            virtualenv('pip install -r requirements.txt')


def local_settings():
    with settings(user=SSH_USER):
        with cd(env.manage_dir):
            upload_template(
                'src/local_settings.py.sample',
                'local_settings.py',
                globals(),
                backup=False
            )


def nginx():
    with settings(user='ubuntu'):
        sudo('cp %(directory)s/tools/nginx/90-d306.conf /etc/nginx/sites-available/90-d306.conf' % env, shell=False)
        #sudo('/etc/init.d/nginx restart')


def runit():
    with settings(user='ubuntu'):
        sudo('cp %(directory)s/tools/runit/run /etc/sv/d306/run' % env, shell=False)


def manage_py(command):
    virtualenv('cd %s && python manage.py %s' % (env.manage_dir, command))


def dump():
    with settings(user=SSH_USER):
        with cd(env.directory):
            tmp_filename = run("date +/tmp/d306_backup_%Y%m%d_%H%M.sql.gz")
            month_dir = date.today().strftime("%Y_%m")
            backup_dir = "Backup/db/%s" % month_dir
            webdav_command =\
            "import easywebdav;"\
            "webdav = easywebdav.connect('webdav.yandex.ru', username='%s', password='%s', protocol='https');"\
            "webdav.mkdirs('%s');"\
            "webdav.upload('%s', '%s/%s');" % (DUMP_ACCOUNT_NAME, DUMP_PASSWORD, backup_dir, tmp_filename, backup_dir, tmp_filename.split('/')[-1])

            run("mysqldump -u %(DATABASE_USER)s -p%(DATABASE_PASSWORD)s -h %(DATABASE_HOST)s %(DATABASE_DB)s | gzip > " % globals() + tmp_filename)
            virtualenv('python -c "%s"' % webdav_command)
            run("rm %s" % tmp_filename)


def migrate():
    with settings(user=SSH_USER):
        manage_py('syncdb')
        manage_py('migrate')


def restart():
    with settings(user=SSH_USER):
        run('sudo sv restart d306')
        run('chmod 777 /home/madera/projects/d306/fcgi.sock')


def local_env():
    with settings(warn_only=True):
        local('c:\\python\\python virtualenv.py ENV --system-site-packages')
    local('ENV\\Scripts\\pip install -r requirements.txt ')


def update_local_db():
    with settings(user='ubuntu'):
        run("mysqldump -u %(DATABASE_USER)s -p%(DATABASE_PASSWORD)s -h %(DATABASE_HOST)s %(DATABASE_DB)s > dump.sql" % globals())
        get("dump.sql", "dump.sql")
        run("rm dump.sql")
        local("mysql -uroot %(DATABASE_DB)s < dump.sql" % globals())
        local("del dump.sql")


def ftp():
    with settings(user='ubuntu'):
        sudo('apt-get install -y proftpd')

        sed('/etc/proftpd/proftpd.conf', 'ListOptions\\s+"-l"', 'ListOptions "-la"', use_sudo=True)
        uncomment('/etc/proftpd/proftpd.conf', 'DefaultRoot', use_sudo=True)
        uncomment('/etc/proftpd/proftpd.conf', 'RequireValidShell', use_sudo=True)
        uncomment('/etc/proftpd/proftpd.conf', 'PassivePorts', use_sudo=True)
        append('/etc/proftpd/proftpd.conf', 'AuthOrder  mod_auth_file.c', use_sudo=True)
        append('/etc/proftpd/proftpd.conf', 'AuthUserFile  /etc/proftpd/proftpd.passwd', use_sudo=True)
        append('/etc/proftpd/proftpd.conf', 'AuthGroupFile  /etc/proftpd/proftpd.group', use_sudo=True)
        sudo('touch /etc/proftpd/proftpd.passwd')
        sudo('touch /etc/proftpd/proftpd.group')
        sudo('chown -R root:root  /etc/proftpd')
        sudo('chmod 0660 /etc/proftpd/proftpd.passwd')
        sudo('chmod 0660 /etc/proftpd/proftpd.group')
        sudo('chmod 0660 /etc/proftpd/proftpd.conf')
        run('mkdir -p /home/%s/projects' % SSH_USER)
        sudo('echo "%s" | ftpasswd --name %s --home /home/%s/projects --uid 1002 --gid 1002 --file /etc/proftpd/proftpd.passwd --shell /sbin/nologin --DES --passwd --stdin' % (FTP_PASSWORD, FTP_LOGIN, SSH_USER))
        append('/etc/proftpd/proftpd.group', 'tester:*:1002:\n', use_sudo=True)
        sudo('/etc/init.d/proftpd restart')