"""Execute the shipped MenuActionRequest action-selection block under Unicorn.

Runtime helpers (managed string comparison, unboxing, allocation, send) are stubs;
all branching and constructor argument selection are original x86 instructions.
No client execution, network connection, DLL patch or game state mutation occurs.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_trial/drone-deps'))
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
DLL=ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll'
raw=DLL.read_bytes();pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
# Other independent .115 compatibility patches may change the DLL identity;
# require the exact original native function before executing this fixed layout.
start=pe.get_offset_from_rva(0x3780a0);end=pe.get_offset_from_rva(0x378230)
ACTION_SHA256='c4e0782e16732d5e0b593359aa3728453ee4139b7103c2beb192ec7a92045388'
if hashlib.sha256(raw[start:end]).hexdigest()!=ACTION_SHA256:
 raise ValueError('Unsupported native MenuActionRequest function fingerprint')

def probe(style,bar,double):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(pe.OPTIONAL_HEADER.SizeOfImage+0xfff)&~0xfff);u.mem_write(base,pe.get_memory_mapped_image())
 u.mem_map(0x70000000,0x20000);u.mem_write(0x134fadc9,b'\x01')
 def w(p,v):u.mem_write(p,struct.pack('<I',v))
 def r(p):return struct.unpack('<I',u.mem_read(p,4))[0]
 pointers={'selection':0x70001000,'toogle':0x70001100,'oneShot':0x70001200,'categoryBar':0x70001300,'standardSlotBar':0x70001400,'premiumSlotBar':0x70001500,'timer':0x70001600}
 for address,value in {0x133e5634:pointers['selection'],0x13406aa0:pointers['toogle'],0x133e13a0:pointers['oneShot'],0x1341045c:pointers['categoryBar'],0x133c8738:0x70002000,0x133d9b98:0x70002100,0x133e4f7c:0x70002200}.items():w(address,value)
 w(0x70002020,1);w(0x70002274,1)
 # Box class +20 must match SendMenuActionRequest type; unboxing returns payload.
 w(0x70003000,0x70003100);w(0x70003120,1)
 w(0x70004000,0x70005000);w(0x70004004,0x70006000);w(0x70004008,int(double));w(0x7000400c,pointers[bar]);w(0x70006008,pointers[style]);w(0x70006030,0x70007000)
 stack=0x7001e000;w(stack,0x70000100);w(stack+4,0x70008000);w(stack+8,0x70003000);u.reg_write(UC_X86_REG_ESP,stack)
 out={}
 def hook(uc,address,size,user):
  esp=uc.reg_read(UC_X86_REG_ESP)
  if address==0x70000100:uc.emu_stop();return
  result=None
  if address==0x101eec30:result=0x70004000
  elif address==0x1208d730:result=int(r(esp+4)==r(esp+8))
  elif address==0x12093750:result=int(r(esp+4)!=r(esp+8))
  elif address==0x101ac3a0:result=0x70009000
  elif address==0x1168a540:
   out.update(menuItemId=r(esp+8),actionType=r(esp+12),sourceType=r(esp+16));result=r(esp+4)
  elif address==0x102c8ef0:out['sent']=True;result=0
  elif address==0x101ef950:result=0
  elif address==0x101ef8a0:raise AssertionError('Native null reference')
  elif address==0x101eeac0:raise AssertionError('Native type mismatch')
  if result is not None:
   uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_EIP,r(esp));uc.reg_write(UC_X86_REG_ESP,esp+4)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x103780a0,0,count=10000)
 assert out.get('sent'),out
 return dict(style=style,bar=bar,doubleClick=double,actionType=out['actionType'],sourceType=out['sourceType'])


@lru_cache(maxsize=4)
def _mapped_user_image(image,base):
 p=pefile.PE(data=image,fast_load=True)
 mapped=bytearray(p.get_memory_mapped_image())
 if base!=p.OPTIONAL_HEADER.ImageBase:
  # Apply the shipped HIGHLOW records to every executed original method.
  # Runtime helper bodies are stubbed; their unexecuted bytes need no rebasing.
  directory=p.OPTIONAL_HEADER.DATA_DIRECTORY[5]
  relocs=p.get_data(directory.VirtualAddress,directory.Size)
  ranges=((0x10bf650,0x10bf687),(0x10c04a0,0x10c0869));cursor=0
  while cursor<len(relocs):
   page,size=struct.unpack_from('<II',relocs,cursor)
   if not size:break
   if any((start&~4095)<=page<end for start,end in ranges):
    for (entry,) in struct.iter_unpack('<H',relocs[cursor+8:cursor+size]):
     rva=page+(entry&4095)
     if entry>>12==3 and any(start<=rva<end for start,end in ranges):
      struct.pack_into('<I',mapped,rva,struct.unpack_from('<I',mapped,rva)[0]+base-p.OPTIONAL_HEADER.ImageBase)
   cursor+=size
 return bytes(mapped),p.OPTIONAL_HEADER.SizeOfImage


def probe_user_item(image, item_id, double=False, bar='categoryBar', base=0x10000000,
                    callback=False, null_context=None, flags=0x646, guard_only=False):
 """Execute actual click delegates/UserItem; managed runtime calls are stubs.

 Shipped PE relocations for executed methods are applied at alternate bases. guard_only
 observes the unchanged prologue continuation or ignored-return boundary and
 checks machine context without running the original method's side effects.
 """
 mapped,image_size=_mapped_user_image(image,base)
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 u.mem_map(base,(image_size+4095)&~4095);u.mem_write(base,mapped)
 heap=0x70000000;u.mem_map(heap,0x30000)
 def w(address,value):u.mem_write(address,struct.pack('<I',value))
 def r(address):return struct.unpack('<I',u.mem_read(address,4))[0]
 current=heap+0x10000
 def string(value):
  nonlocal current
  ptr=current;data=value.encode('utf-16le');current+=len(data)+32
  u.mem_write(ptr,b'\0'*8+struct.pack('<I',len(data)//2)+data+b'\0\0');return ptr
 pointers={name:string(name) for name in ('categoryBar','standardSlotBar','premiumSlotBar','proActionBar')}
 for i,global_rva in enumerate((0x33cb8fc,0x33f7b98,0x33e8940,0x3419bcc,0x33f6380,0x3402aac)):
  cls=heap+0x1000+i*0x400;static=cls+0x100
  w(base+global_rva,cls);w(cls+0x74,1);w(cls+0x5c,static)
  if global_rva==0x3419bcc:w(static+0x28,heap+0x9000)
  if global_rva==0x33f6380:w(static+0xc,heap+0x9100)
  if global_rva==0x3402aac:w(static+0x74,heap+0x9200)
 for initialized in (0x34fe2b5,0x34fa678):u.mem_write(base+initialized,b'\x01')
 for global_rva,name in ((0x341045c,'categoryBar'),(0x33eafb0,'standardSlotBar'),
                         (0x340425c,'premiumSlotBar'),(0x34054b0,'proActionBar')):
  w(base+global_rva,pointers[name])
 obj,item,grid=heap+0x6000,heap+0x7000,heap+0x8000
 w(obj+0x80,0 if null_context=='item' else item);w(obj+0x98,grid)
 w(item+0x30,string(item_id) if item_id is not None else 0)
 w(grid+0x40,{'categoryBar':0,'standardSlotBar':1,'premiumSlotBar':2,'proActionBar':3}[bar])
 esp=heap+0x2e000;sentinel=heap+0x100
 u.mem_write(esp,struct.pack('<IIII',sentinel,0 if null_context=='this' else obj,
                            0x12340000|int(double),0x12345678))
 regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
       UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
 values=[0x11110000+i for i in range(len(regs))]
 for reg,value in zip(regs,values):u.reg_write(reg,value)
 for i in range(8):u.reg_write(UC_X86_REG_XMM0+i,int.from_bytes(bytes([i+1])*16,'little'))
 u.reg_write(UC_X86_REG_ESP,esp);u.reg_write(UC_X86_REG_EFLAGS,flags)
 before=bytes(u.mem_read(obj,0x3000));events=[];out={'events':events}
 def hook(uc,address,size,user):
  stack=uc.reg_read(UC_X86_REG_ESP);target=address-base;result=None
  if address==sentinel:
   out['ignored']=True;uc.emu_stop();return
  if guard_only and target==0x10c04a6:
   out['ignored']=False;uc.emu_stop();return
  if target in (0x1eea70,0x1ef950):result=0
  elif target==0x2924eb0:result=0
  elif target==0x1eea40:
   ptr=r(stack+8);result=heap+0xa000 if not events else heap+0xb000
   # Distinct boxed enum and event storage, as in the native method.
   if r(ptr)==5:result=heap+0xa000;w(result,5)
   else:result=heap+0xb000;u.mem_write(result,bytes(u.mem_read(ptr,16)))
  elif target==0x73a0e0:
   payload=r(stack+12);data=bytes(u.mem_read(payload,16))
   events.append(dict(item=r(payload+4),doubleClick=bool(data[8]),bar=r(payload+12)))
   result=0
  elif target==0x17b13a0:result=heap+0x9300
  elif target==0x208d730:result=int(r(stack+4)==r(stack+8))
  elif target==0x1ef8a0:raise AssertionError('Native null reference')
  if result is not None:
   uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_EIP,r(stack));uc.reg_write(UC_X86_REG_ESP,stack+4)
 u.hook_add(UC_HOOK_CODE,hook)
 entry=0x10bf670 if double else 0x10bf650
 u.emu_start(base+(entry if callback else 0x10c04a0),0,count=10000)
 out.update(registers=[u.reg_read(reg) for reg in regs],initial_registers=values,
            flags=u.reg_read(UC_X86_REG_EFLAGS),esp_delta=u.reg_read(UC_X86_REG_ESP)-esp,
            xmm=[u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)],
            context_unchanged=before==bytes(u.mem_read(obj,0x3000)),
            expected_item=item,expected_bar=pointers[bar])
 return out
if __name__ == '__main__':
 results=[probe(style,bar,double) for style in ('selection','oneShot','toogle','timer') for bar in ('categoryBar','standardSlotBar','premiumSlotBar') for double in (False,True)]
 print(json.dumps(dict(dll_sha256=hashlib.sha256(raw).hexdigest(),entry='0x103780a0',limits='Managed runtime helpers stubbed; original native branch instructions executed; static emulation does not establish live UI behavior.',cases=results),indent=2))
