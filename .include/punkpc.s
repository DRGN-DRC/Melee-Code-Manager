.ifndef punkpc.library.included
.ifndef punkpc.module.version
.include "punkpc/library.s"
.endif
module.library punkpc, ".s", ppc
.endif
punkpc.subdir "punkpc/", ".s"
