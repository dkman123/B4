BigBrotherBot (B4) management script
====================================

In this directory you can find a BASH script which can help you dealing with B4 on Linux systems.  
In particular 2 BASH scripts needs some more attention:

Such BASH script provides a set of tools which can help you managing your B4 instances on a Linux system.  
They allow you to: 

* Launch multiple B4 instances (as background processes).
* Shutdown gracefully alive B4 instances.
* Monitor the status of your B4 instances (and list the available ones).
* Clean B4 directory from Python compiled sources _(only for the source distribution)_.
* Check for the correct Python interpreter to be available _(only for the source distribution)_.
* Prevent you from running B4 instances as **root**.

### Requirements

* Linux (tested on Debian, Ubuntu)
* [Bash](https://www.gnu.org/software/bash/): usually installed by default
* [bc](https://www.gnu.org/software/bc/manual/html_mono/bc.html) shell command: `apt-get install bc` on Debian based distro
* [Screen](http://linux.die.net/man/1/screen) window manager

In order for B4 to work correctly using this script you need to setup a Linux system user that will run B4. Such user
will have to be proprietory of all the B4 files. If for example your system user is **b4** and belongs to the group **users** 
you can then change ownership of all the B4 files to belong to the **b4** user by typing the following in the Linux console: 
`chown -R b4:users /path/to/main/b4/directory`. For information on how to add a Linux system user, please refer to
the [man page](http://linux.die.net/man/8/useradd).

### How to use

As described above, the script will allow you to launch multiple B4 instances so you can manage multiple game servers.
In order to do that you need to specify multiple B4 configuration files to be used to start B4 instances: those 
configuration files can be placed under the following paths:
 
* Main B4 configuration directory (namely `b4/conf`)
* B4 home directory: if the system user running B4 is **b4**, the B4 home directory will b4 `/home/b4/.b4/`.
 
The names of the configuration files needs to follow a specific pattern: `b4_[<name>].[.ini|.xml]`.  

As an example let's assume you are running **2** game servers and you need to start **2** B4 intances: let's call them 
**tdm** and **ctf**. What you need to do is pretty simple: you need to create **2** configuration files (one for each instance):

* create a `b4_tdm.xml` or `b4_tdm.ini` for the **tdm** instance
* create a `b4_ctf.xml` or `b4_ctf.ini` for the **ctf** instance

*NOTE: you can obviously customize those configuration files as you want hence you can load different plugins and 
different plugin configuration files on every B4 instance you intend to run.*

After saving the configuration files, you are ready to launch your B4 instances using the `b4.sh` script: the script 
autodiscovers new configuration files and let you interact with them by using the chosen B4 instance name as input parameter.
So, in the example above you can launch the **tdm** and **ctf** B4 instances by typing:

* `./b4.sh start tdm`
* `./b4.sh start ctf`

The script will inform you on the result of the startup operation: you can then check the status of the B4 processes
using the `status` command provided by the `b4.sh` script.  
Note that the B4 instance `<name>` parameter is optional: if you do not specify it the script will execute the given 
operation on all the B4 instances it can find (so in the previous example you could have just typed `./b4.sh start` to 
start both the **tdm** and **ctf** B4 instances.

### Commands reference

```bash
-usage: b4.sh  start   [<name>] - start B4
               stop    [<name>] - stop B4
               restart [<name>] - restart B4
               status  [<name>] - display current B4 status
               clean            - clean B4 directory (only for the source distribution)
```

### For advanced users

* You can disable B4 autorestart mode by setting the `B4_AUTORESTART` environment variable to `0` (in the system user 
  `.bash_profile`): after doing so B4 won't restart automatically after a crash.
* You can enable logging by setting the `B4_LOG` environment variable to `1` (in the system user `.bash_profile`): log 
  will be available in `b4/scripts/log/app.log` and will contain the console output produced by the BASH script.
* You can turn off bash colors by setting the `USE_COLORS` variable to `0` (in the BASH script): while the usage is 
  advised for a fast reading and understanding of the console output, some people may not like them.
* If you want to be able to control all your B4 instances no matter the current working directory you can setup an alias
  in your system user `.bash_profile`: `alias b4='/path/to/main/b4/directory/scripts/b4.sh'`. You can then, as an example,
  check the status of all your B4 instances by typing `b4 status` no matter the directory you are in.

_[www.bigbrotherbot.net](http://www.bigbrotherbot.net/) (2005-2011)_
