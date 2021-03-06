import wx
class genericCopyID():

    def __init__(self,pubkey,username,host,displayStrings,parent,*args,**kwargs):
        self.username=username
        self.host=host
        self.displayStrings=displayStrings
        self.pubkey=pubkey
        self.parent=parent

    def getPass(self,queue):
        dlg=wx.PasswordEntryDialog(self.parent,self.displayStrings.passwdPrompt)
        retval=dlg.ShowModal()
        if retval==wx.ID_OK:
            queue.put(dlg.GetValue())
        else:
            queue.put(None)
        dlg.Destroy()

    def copyID(self):

        import ssh
        import Queue
        sshClient = ssh.SSHClient()
        sshClient.set_missing_host_key_policy(ssh.AutoAddPolicy())
        password=""
        notConnected=True
        while notConnected:
            queue=Queue.Queue()
            try:
                sshClient.connect(hostname=self.host,timeout=10,username=self.username,password=password,allow_agent=False,look_for_keys=False)
                notConnected=False
            except ssh.AuthenticationException:
                wx.CallAfter(self.getPass,queue)
                password=queue.get()
                if password==None:
                    raise Exception("Login Canceled")

        # SSH keys won't work if the user's home directory is writeable by other users.
        writeableDirectoryErrorMessage = "" + \
            "Your home directory is writeable by users other than yourself. " + \
            "As a result, you won't be able to authenticate with SSH keys, so you can't use the Launcher. " + \
            "Please correct the permissions on your home directory, e.g.\n\n" + \
            "chmod 700 ~"
        (stdin,stdout,stderr)=sshClient.exec_command('ls -ld ~ | grep -q "^d....w" && echo HOME_DIRECTORY_WRITEABLE_BY_OTHER_USERS')
        err=stdout.readlines()
        if err!=[]:
            raise Exception(writeableDirectoryErrorMessage)
        (stdin,stdout,stderr)=sshClient.exec_command('ls -ld ~ | grep -q "^d.......w" && echo HOME_DIRECTORY_WRITEABLE_BY_OTHER_USERS')
        err=stdout.readlines()
        if err!=[]:
            raise Exception(writeableDirectoryErrorMessage)

        (stdin,stdout,stderr)=sshClient.exec_command("module load massive")
        err=stderr.readlines()
        if err!=[]:
            pass
        (stdin,stdout,stderr)=sshClient.exec_command("/bin/mkdir -p ~/.ssh")
        err=stderr.readlines()
        if err!=[]:
            raise Exception
        (stdin,stdout,stderr)=sshClient.exec_command("/bin/chmod 700 ~/.ssh")
        err=stderr.readlines()
        if err!=[]:
            raise Exception
        (stdin,stdout,stderr)=sshClient.exec_command("/bin/touch ~/.ssh/authorized_keys")
        err=stderr.readlines()
        if err!=[]:
            raise Exception
        (stdin,stdout,stderr)=sshClient.exec_command("/bin/chmod 600 ~/.ssh/authorized_keys")
        err=stderr.readlines()
        if err!=[]:
            raise Exception
        (stdin,stdout,stderr)=sshClient.exec_command("/bin/echo \"%s\" >> ~/.ssh/authorized_keys"%self.pubkey)
        err=stderr.readlines()
        if err!=[]:
            raise Exception('The program was unable to write a file in your home directory. This might be because you have exceeded your disk quota. You should log in manually and clean up some files if this is the case')
        sshClient.close()
