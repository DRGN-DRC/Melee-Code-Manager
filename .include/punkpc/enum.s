.ifndef ndef;
  .macro ifdef,sym;.altmacro;ifdef.alt \sym;.noaltmacro;.endm;
  .macro ifdef.alt,sym;def=0;.ifdef sym;def=1;.endif;ndef=def^1;.endm;
  # --- ifdef object - alternative to .ifdef that prevents errors caused by '\' in .ifdef statements
  # updates properties 'def' and 'ndef' for use as evaluatable properties in .if statements
  # ifdef \myObjectName\().exists
  # # create a numerically evaluable property out of a problematic symbol name
  # .if def;  # then given symbol exists
  # .if ndef; # then given symbol does not exist
  # - if calling in .altmacro mode, use the 'ifdef.alt' variant
.endif

ifdef enumb.v
.if ndef
  .macro enum,va:vararg;.irp a,\va;a=1;.irpc c,\a;.irpc i,-+;.ifc \c,\i;enum.i=\a;a=0;.endif;
  .ifc \c,(;enum.v=\a;a=0;.endif;.endr;.exitm;.endr;.if a;\a=enum.v;enum.v=enum.v+enum.i;.endif;
  .endr;.endm;enum.v=0;enum.i=1; # --- enumerator object:
  # updates properties 'enum.v' counter and 'enum.i' increment amount
  # enum A B C D  # enumerate given symbols with incrementing value;  start with '.v= 0; .i= +1'
  # enum E F G H  # next call will continue previous enumerations
  # # >>>  A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7
  # enum (31)     # re-orient enumeration value '.v=n' with parentheses ( )
  # enum -4       # set enumeration to increment/decrement '.i=n' by a specific amount with +/-
  # enum I, +1, J K L
  # # >>>  I=31, J=27, K=28, L=29
  # enum (31),-1,rPlayer,rGObj,rIndex,rCallback,rBools,rCount
  # # register names ...
  # sp.xWorkspace=0x220
  # enum (sp.xWorkspace),+4,VelX,VelY,RotX,RotY,RGBA
  # # offset names ...
  # # etc..

  .macro enumb,va:vararg;.irp a,\va;a=1;.irpc c,\a;.irpc i,-+;.ifc \c,\i;enumb.i=\a;a=0;.endif;
  .ifc \c,(;enumb.v=\a;a=0;.endif;.endr;.exitm;.endr;.if a;b\a=enumb.v;enumb.v=enumb.v+enumb.i;
  m\a=0x80000000>>b\a;.endif;.endr;.endm;# --- bool enumerator object:
  # enumb Enable, UseIndex, IsStr       # state the bool symbol names you want to use
  # # >>> bEnable   = 31; mEnable   = 0x00000001
  # # >>> bUseIndex = 30; mUseIndex = 0x00000002
  # # >>> bIsStr    = 29; mIsStr    = 0x00000004
  # # mMask and bBit symbols are created for each
  # enumb (0), +1, A, B, C
  # # >>> bA = 0; mA = 0x80000000
  # # >>> bB = 1; mB = 0x40000000
  # # >>> bC = 2; mC = 0x20000000
  # .long mA|mB|mC
  # # >>> 0xE0000000
  # rlwinm. r3, r0, 0, bUseIndex, bUseIndex
  # rlwinm. r3, r0, 0, mUseIndex
  # # both of these rlwinms are identical
  # rlwimi r0, r0, bIsStr-bC, mC
  # # insert bIsStr into bC in a single register/instruction

  .macro enumb.mask,va:vararg;i=0;.irp a,\va;ifdef \a;
  .if ndef;\a=0;.endif;ifdef m\()\a;.if ndef;m\()\a=0;.endif;i=i|(m\a&(\a!=0));.endr;enumb.mask=i;
  enumb.crf=0;.rept 8;enumb.crf=(enumb.crf<<1)|!!(i&0xF);i=i<<4;.endr;.endm;enumb.v=31;enumb.i=-1;
  # --- mask generator:
  # enumb Enable, UseIndex, IsStr       # state the bool symbol names you want to use
  # Enable = 1; UseIndex = 1;           # set some boolean values as T/F
  # # unassigned bool IsStr is assumed to be 0
  # enumb.mask Enable, UseIndex, IsStr  # generate a mask with said bools using 'enumb.mask'
  # # this uses the mMask value and the state values to create a combined state mask
  # m=enumb.mask;  .long m              # mask will compile from given 'enumb' index values
  # # you can save the combined mask by copying the return enumb.mask property
  # # >>> 0x00000003
  # crf=enumb.crf;  mtcrf crf, r0
  # # you can move partial fields directly into the volatile CR registers with mtcrf, and enumb.crf
  # bf- bEnable, 0f
  #   bf- bIsStr, 1f; nop; 1:
  #   bt+ bUseIndex, 0f; nop; 0:
  # # once in the CR, each bool can be referenced by name in 'bf' or 'bt' branch instructions
.endif
