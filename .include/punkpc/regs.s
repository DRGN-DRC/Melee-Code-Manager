.ifndef punkpc.library.included
  .include "punkpc.s";.endif;punkpc.module regs, 1
.if module.included == 0;  punkpc xem, enum
  .macro regs.enumerate,  pfx,  sfx,  start=0,  op="+1",  cstart,  cop,  count=32
    .ifb \cop;  regs.enumerate \pfx, \sfx, \start, \op, \cstart, \op, \count;.exitm;.endif;
    .ifb \cstart;  regs.__c = \start
    .else;  regs.__c = \cstart;.endif;regs.__i=\start
    .rept \count;  xem \pfx, regs.__i, "<\sfx=regs.__c>"
      regs.__i = regs.__i\op;regs.__c = regs.__c\cop;.endr;
  .endm;.macro regs.rebuild
    .irpc c,  rfb;  regs.enumerate \c;.endr;regs.enumerate pfx=m, cstart=0x80000000, cop=">>1"
    regs.enumerate pfx=cr, count=8;sp=r1;rtoc=r2;lt=0;gt=1;eq=2;so=3;xem = 0
    .rept 8
      .irp s,  lt,  gt,  eq,  so;  xem cr, xem, "<.\s=(xem*4)+\s>"
      .endr;xem = xem + 1;.endr;
  .endm;regs.rebuild;enum.new regs, , , (3), +1;.endif

