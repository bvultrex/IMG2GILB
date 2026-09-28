"""Windows child-process lifetime guard; only processes started by this app are assigned."""
import ctypes,os
from ctypes import wintypes as W
if os.name=='nt':
 K=ctypes.WinDLL('kernel32',use_last_error=True)
 class Basic(ctypes.Structure):_fields_=[('per_process',ctypes.c_int64),('per_job',ctypes.c_int64),('flags',W.DWORD),('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
 class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ['read_op','write_op','other_op','read_bytes','write_bytes','other_bytes']]
 class Extended(ctypes.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
 K.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];K.CreateJobObjectW.restype=W.HANDLE
 K.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];K.SetInformationJobObject.restype=W.BOOL
 K.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];K.AssignProcessToJobObject.restype=W.BOOL
 K.CloseHandle.argtypes=[W.HANDLE];K.CloseHandle.restype=W.BOOL
 K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenProcess.restype=W.HANDLE
 K.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
 K.GetExitCodeProcess.argtypes=[W.HANDLE,ctypes.POINTER(W.DWORD)]
def identity(pid):
 if os.name!='nt':return None
 h=K.OpenProcess(0x1000,False,pid)
 if not h:return None
 try:
  times=[W.FILETIME() for _ in range(4)];code=W.DWORD()
  if not K.GetProcessTimes(h,*[ctypes.byref(t) for t in times]) or not K.GetExitCodeProcess(h,ctypes.byref(code)) or code.value!=259:return None
  return {'pid':pid,'created':(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime}
 finally:K.CloseHandle(h)
class ProcessGuard:
 def __init__(self,process):
  self.handle=None
  if os.name!='nt':return
  self.handle=K.CreateJobObjectW(None,None);limits=Extended();limits.basic.flags=0x2000
  if not self.handle or not K.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not K.AssignProcessToJobObject(self.handle,int(process._handle)):
   self.close();process.terminate();process.wait();raise OSError(ctypes.get_last_error(),'Cannot protect worker process lifetime')
  nt=ctypes.WinDLL('ntdll');nt.NtResumeProcess.argtypes=[W.HANDLE];nt.NtResumeProcess.restype=ctypes.c_long
  if nt.NtResumeProcess(int(process._handle))<0:
   self.close();process.wait();raise RuntimeError('Cannot resume protected worker')
 def close(self):
  if self.handle:K.CloseHandle(self.handle);self.handle=None
