.ifndef xev
  .macro xev,b=xe.beg,e=-1,va:vararg;xe.beg=\b;xe.end=\e&(-1>>1);xe.len=xe.beg-1;xev=-1;xe.ch,\va
  .endm;.macro xe.ch,e,va:vararg;xe.i=-1;xe.len=xe.len+1;.irpc c,\va;xe.i=xe.i+1;.if xe.i>xe.end
    .exitm;.elseif xe.i>=xe.len;xe.ch "\e\c",\va;.endif;.endr;.if xev==-1;xev=\e;.endif
  .endm;.irp x,beg,end,len;xe.\x=0;.endr;xev=-1
  # --- xev: extract eXpression and EValuate - xev [begin char idx], [inclusive end idx], [str]
  #  substring is extracted from body and evaluated through the 'xev' property
  # # Examples:
  # xev 5,6,myVal16; .long xev
  # # expression '16' is extracted from symbol name 'myVal16'
  # xev 5,,myVal17; .long xev
  # # blank end index selects end of string
  # xev,,myVal18; .long xev
  # # blank beginning index reselects last used beginning index; or 0 default
  # # >>> 00000010 00000011 00000012
.endif

.ifndef xr.reg; xr.reg=0
  .macro idxr, xr; .irp s,len,beg,dep,end,idx,reg; xr.\s=-1;.endr; .irpc c,\xr; xr.len=xr.len+1
      .ifc (,\c; xr.dep=xr.dep+1; .if xr.dep==0; xr.beg=xr.len+1; xr.end=-1; .endif; .endif
      .ifc ),\c; xr.dep=xr.dep-1; .if xr.dep==-1; xr.end=xr.len-1; .endif; .endif
    .endr; xev 0,xr.beg-2,\xr; xr.idx=xev; xev xr.beg,xr.end,\xr; xr.reg=xev;.endm
  # --- idxr: InDeX of Register (i/o syntax) - 'idxr x(r)'  becomes->  xr.idx=x  xr.reg=r
  #  evaluates 'x' separately from 'r' from given input
  #  right-most parentheses '( )' captures 'r'
  #  input does not need to be quoted if there are no spaces between idx and reg
  #  outputs return properties 'xr.idx' and 'xr.reg'
  # # Examples:
  # # first create macro 'test' that uses 'idxr' to extract inputs:
  # .macro test,xr; idxr \xr; .long xr.idx, xr.reg;.endm
  # test 0x400(31); test (0x100<<2)((3+29))
  # # >>> 00000400 0000001F 00000400 0000001F
.endif
