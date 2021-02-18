.ifndef punkpc.library.version;  punkpc.library.version = 0;.endif;
.ifeq punkpc.library.version;  punkpc.library.version = 2;module.included = 1;_punkpc = .
  .macro module.library,  self,  ext=".s",  default:vararg
    .macro \self,  va:vararg
      .ifb \va
        .ifnb \default;  \self \default;.endif;
      .else;  .irp m,  \va
          .ifnb \m;  module.included "\self", ".\m", ".version"
            .if module.included == 0;  \self\().build_pathstr \m;.endif;.endif;.endr;.endif;
    .endm;.macro \self\().raw,  va:vararg
      .irp args,  \va;  module.raw.build_args \self, \args;.endr;
    .endm;.macro \self\().module,  m,  version=1;  module.included "\self", ".\m", ".version"
      .if module.included == 0
        .irp vsn ".version";  \self\().\m\vsn = \version;.endr;.endif;
    .endm;.macro \self\().subdir,  sub,  ex;  .purgem \self\().build_pathstr
      .macro \self\().build_pathstr,  str,  s="\sub",  e="\ex",  lude="lude",  args
        .inc\lude "\s\str\e" \args
      .endm;.endm;.macro \self\().build_pathstr;  .endm;\self\().subdir \self\()/
    \self\().library.included = 1
  .endm;.macro module.included,  __mdul_pfx,  __mdul_mid,  __mdul_suf=".version";  .altmacro
    module.included.alt \__mdul_pfx\__mdul_mid\__mdul_suf;.noaltmacro
    .if module.included
      .if \__mdul_pfx\__mdul_mid\__mdul_suf == 0;  module.included = 0;.endif;.endif;
  .endm;.macro module.included.alt,  __mdul_vsn;  module.included = 0
    .ifdef __mdul_vsn;  module.included = 1;.endif;
  .endm;.macro module.raw.build_args,  self,  file,  va:vararg
    .ifb \va;  \self\().build_pathstr \file, , , "bin"
    .else;  \self\().build_pathstr \file, , , "bin", ", \va";.endif;
  .endm;.endif;

