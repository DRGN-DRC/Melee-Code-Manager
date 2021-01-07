.ifndef dbg.included; dbg.included=1
  .macro dbg,i,x;.ifb \x;.altmacro;dbg %\i,\i;.noaltmacro;.else;.error "\x = \i";.endif;.endm
  # --- dbg: DeBuG expression - dbg [expression]
  #  prints an error "[expression] = (evaluation)" -- useful for debugging
  # i=0x1337; dbg i
  # # >>>  (error message: i = 4919)
.endif
