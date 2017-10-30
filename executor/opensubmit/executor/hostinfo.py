'''
    Functions to retrieve host information.
'''

import platform

def from_cmd(cmd, stdhndl=" 2>&1", e_shell=True):
    '''
        Determine some system information based on a shell command.
    '''
    try:  
        p = subprocess.Popen(cmd + stdhndl, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=e_shell)
        p.wait()
        out = "".join([p.stdout.read(),p.stderr.read()]).decode("utf-8",errors="ignore")
        if p.returncode!=0:
            out=""
        return out
    except Exception as e:
        return ""

def ipaddress():
    ''' 
        Determine our own IP adress. This seems to be far more complicated than you would think:
    '''
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com",80))
        result = s.getsockname()[0]
        s.close()
        return result
    except Exception as e:
        return ""

def opencl():
    '''
        Determine some system information about the installed OpenCL device.
    '''
    result=[]
    try:
        import pyopencl as ocl
        for platform in ocl.get_platforms():
            result.append("Platform: "+platform.name)
            for device in platform.get_devices():
                result.append("    Device:" + device.name.strip())
                infoset = [key for key in dir(device) if not key.startswith("__") and key not in ["extensions", "name"]]
                for attr in infoset:
                    try:
                        result.append("        %s: %s"%(attr.strip(), getattr(device, attr).strip()))
                    except:
                        pass
        return "\n".join(result)
    except Exception as e:
        return ""

def os():
    conf = platform.uname()
    return "%s %s %s (%s)"%(conf[0], conf[2], conf[3], conf[4])

def cpu():
    try:
       from cpuinfo import cpuinfo
       cpu=cpuinfo.get_cpu_info()
       return "%s, %s, %s Family %d Model %d Stepping %d #%d" % (cpu["brand"],cpu["vendor_id"],cpu["arch"],cpu['family'],cpu['model'],cpu['stepping'],cpu["count"])
    except:
       return platform.processor() #may be empty on Linux because of partial implemtation in platform

def compiler():
    if platform.system()=="Windows":
       conf = from_cmd("cl.exe|@echo off","") #force returncode 0
       conf = conf.split("\n")[0] #extract version info
    else:
       conf = from_cmd("cc -v")
    return conf 

def all_host_infos():
    '''
        Summarize all host information.
    '''
    output = []
    output.append(["Operating system", os()])
    output.append(["CPUID information", cpu()])
    output.append(["CC information", compiler()])
    output.append(["JDK information", from_cmd("java -version")])
    output.append(["MPI information", from_cmd("mpirun -version")])
    output.append(["Scala information", from_cmd("scala -version")])
    output.append(["OpenCL headers", from_cmd("find /usr/include|grep opencl.h")])
    output.append(["OpenCL libraries", from_cmd("find /usr/lib/ -iname '*opencl*'")])
    output.append(["NVidia SMI", from_cmd("nvidia-smi -q")])
    output.append(["OpenCL Details", opencl()])
    return output

