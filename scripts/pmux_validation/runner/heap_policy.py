"""V9 target-only environment and readonly startup heap verification."""
import ctypes,os,struct
REVISION='v9-nodebugheap-r1'
POLICY='windows-no-debug-heap-v1'
def target_environment(env):
    result={k:v for k,v in (os.environ if env is None else env).items() if k.upper()!='_NO_DEBUG_HEAP'}
    result['_NO_DEBUG_HEAP']='1'
    return result

def observation_errors(o,pid):
    if not isinstance(o,dict):return ['heap observation missing']
    errors=[]
    expected={'pid':pid,'layout':'win64-ntheap-v1','verified':True,'heap_signature':0xffeeffee}
    for k,v in expected.items():
        if o.get(k)!=v:errors.append('heap '+k+' mismatch')
    for k,mask in [('ntglobal_flags',0x70),('heap_flags',0x40000060),('heap_force_flags',0x40000060)]:
        v=o.get(k)
        if type(v) is not int or v<0 or v & mask:errors.append(k+' debug flags enabled/unreadable')
    if type(o.get('heap_flags')) is int and not o['heap_flags'] & 2:errors.append('unsupported process heap')
    return errors

def sample_errors(row):
    errors=[]
    for k,v in [('measurement_revision',REVISION),('heap_policy',POLICY),('debug_heap_env','1')]:
        if row.get(k)!=v:errors.append(k+' missing/mismatch')
    return errors+observation_errors(row.get('heap_observation'),row.get('main_pid'))

def observe(process,pid):
    if ctypes.sizeof(ctypes.c_void_p)!=8:raise OSError('heap verification requires Windows x64')
    k=ctypes.WinDLL('kernel32',use_last_error=True);n=ctypes.WinDLL('ntdll')
    k.IsWow64Process.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
    wow=ctypes.c_int()
    if not k.IsWow64Process(process,ctypes.byref(wow)) or wow.value:raise OSError('unsupported target architecture')
    n.NtQueryInformationProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p]
    b=ctypes.create_string_buffer(48)
    if n.NtQueryInformationProcess(process,0,b,48,None):raise OSError('process basic information unavailable')
    if struct.unpack_from('<Q',b,32)[0]!=pid:raise OSError('heap observation PID mismatch')
    peb=struct.unpack_from('<Q',b,8)[0]
    k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    def read(address,size):
        data=ctypes.create_string_buffer(size);done=ctypes.c_size_t()
        if not address or not k.ReadProcessMemory(process,address,data,size,ctypes.byref(done)) or done.value!=size:raise OSError('heap metadata read failed')
        return data.raw
    data=read(peb,192);heap=struct.unpack_from('<Q',data,48)[0];hd=read(heap,120)
    o=dict(pid=pid,layout='win64-ntheap-v1',verified=True,observed_at='initial_debug_breakpoint',peb_address=peb,heap_address=heap,heap_signature=struct.unpack_from('<I',hd,16)[0],ntglobal_flags=struct.unpack_from('<I',data,188)[0],heap_flags=struct.unpack_from('<I',hd,112)[0],heap_force_flags=struct.unpack_from('<I',hd,116)[0])
    o['verified']=not observation_errors(o,pid)
    return o
