.ifndef xem.included; xem.included=1
  .macro xem,p,x,s;.altmacro;xema %\x,\p,\s;.noaltmacro;.endm;.macro xema,x,p,s;\p\x\s;.endm;x=-1
  # --- xem: eXpression EMitter - xem [prefix], [expression], [suffix]
  #  non-expressions may require quoting in both "<quotes and brackets>"
  # # Examples:
  # # first create macro 'x' that uses 'xem' to push and pop
  # .macro x, va:vararg; .ifb \va; .if x>0;   xem "<.long x$>",x;  x=x-1;.endif; .else; .irp a,\va;
  #      .ifnb \a; x=x+1;   xem "<x$>",x,"<=\a>";  .endif; .endr; .endif; .endm
  # x 100, 101, 102, 103
  # # push 4 values
  # x; x; x; x
  # # pop 4 values (FIFO)
  # # >>> 00000067 00000066 00000065 00000064
.rept 32;x=x+1;.irpc c,rfb;xem \c,x,"<=x>";.endr;xem m,x,"<=1!<!<(31-x)>";.endr;sp=r1;rtoc=r2;x=-1
.rept 8;x=x+1;xem cr,x,"<=x>";i=x<<2;.irp s,lt,gt,eq,so;\s=i&3;xem cr,x,"<.\s=i>";i=i+1;.endr;.endr
  # 'xem' also includes helpful enumerations for r-, f-, cr- registers, m- mask bits, and b- bools
  # # >>> r31, f31, b31 = 31;  cr7 = 7;  m0 = 0x80000000; m31 = 0x00000001
.endif
