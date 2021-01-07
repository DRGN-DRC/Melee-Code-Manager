.ifndef bla.included; bla.included=1
  .macro bla, a, b
    .ifb \b;lis r0, \a @h;ori r0, r0, \a @l;mtlr r0;blrl
    .else;  lis \a, \b @h;ori \a, \a, \b @l;mtlr \a;blrl;.endif;.endm;.macro ba, a, b;
    .ifb \b;lis r0, \a @h;ori r0, r0, \a @l;mtctr r0;bctr
    .else;  lis \a, \b @h;ori \a, \a, \b @l;mtctr \a;bctr;.endif;
  .endm;.irp l,l,,;.macro branch\l,va:vararg;b\l\()a \va;.endm;.endr
  # --- bla, ba:  polymorphic Branch (Link) Absolute - bl [addr]  OR  bl [reg], [addr]
  # --- branchl, branch - aliases are also accepted
  # macros override default PPC 'bla' and 'ba' instructions with a gecko-compatible replacement
  # - MCM overrides macro, making gecko-version assemble only outside of MCM
  #   - if optional register is provided as first argument -- MCM syntax can be overridden
  #   - 'branch' and 'branchl' alias may also be used to override MCM syntax
  # # Examples:
  # bla 0x8037a120
  # # MCM will use a placeholder for this -- Gecko will use macro
  # bla r0, 0x8037a120
  # # MCM will not catch this, leaving it to the macro in all cases
.endif
