.ifndef extr.included; extr.included=1
  .macro extr rA,rB,mask=0,i=32,dot;.if \mask;.ifeq (\mask)&1;extr \rA,\rB,(\mask)>>1,\i-1,\dot;
      .else;rlwinm\dot \rA,\rB,(\i)&31,\mask;.endif;.else;li \rA,0;.endif;
  .endm;.macro extr.,rA,rB,m;extr \rA,\rB,\m,,.;.endm;
  # --- extr:  EXTRact small int from mask - extr [regout], [regin], [32-bit mask value]
  #  input a 32-bit (contiguous) mask value, and extract a zero-shifted small int from [regin]
  #  'extr.' variant compares result to 0
  #  null masks cause the immediate '0' to be generated
  # - can be used to abstract away all of the rotation math in 'rlwinm' behind a mask symbol:
  # mMyMask=0x0001FF80
  # extr r31, r3, mMyMask
  # # r31 = 10-bit int extracted from r3, and zero-shifted from position described by mask value
  # extr r3, r3, ~mMyMask
  # # r3 = updated self to zero out the mask position where r31 was extracted from

  .macro insr rA,rB,mask=0,i=0,dot;.if \mask;.ifeq (\mask)&1;insr \rA,\rB,(\mask)>>1,\i+1,\dot;
      .else;rlwimi\dot \rA,\rB,(\i)&31,\mask<<(\i&31);.endif;.endif;
  .endm;.macro insr.,rA,rB,m;extr \rA,\rB,\m,,.;.endm;
  # --- insr: INSeRt small int with mask - insr [regcombined], [reginsertion], [32-bit mask value]
  #  like a reverse 'extr' -- this inserts a zeroed int into a target mask position
  #  'insr.' variant compares result (combination) to 0
  #  null masks cause no instructions to be emitted
  #  - when combined with 'extr' -- this creates an i/o utility for small ints:
  # mMyMask=0x0001FF80
  # extr r31, r3, mMyMask
  # # save extraction in r31
  # li r0, 15
  # insr r3, r0, mMyMask
  # # r3 = updated with new value loaded from immediate in r0
.endif
