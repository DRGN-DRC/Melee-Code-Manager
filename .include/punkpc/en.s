.ifndef punkpc.library.included
  .include "punkpc.s";.endif;punkpc.module en, 1
.if module.included == 0
  .macro en,  va:vararg
    .irp sym,  \va
      .ifnb \sym;  \sym=en.count;en.count=en.count+en.step;.endif;.endr;
  .endm;.macro en.restart;  en.count = en.count.restart;en.step = en.step.restart
  .endm;en.count.restart = 0;en.step.restart = 1;en.restart;.endif

