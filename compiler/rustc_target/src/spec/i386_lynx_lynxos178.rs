use crate::spec::{Cc, LinkerFlavor, Lld, StackProbeType, Target};

pub fn target() -> Target {
    let mut base = super::lynxos178_base::opts();
    base.cpu = "i386".into();
    base.max_atomic_width = Some(32);
    base.add_pre_link_args(LinkerFlavor::Gnu(Cc::Yes, Lld::No), &["-m32"]);
    base.stack_probes = StackProbeType::X86;

    Target {
        llvm_target: "i686-unknown-linux-gnu".into(),
        pointer_width: 32,
        data_layout: "e-m:e-p:32:32-p270:32:32-p271:32:32-p272:64:64-\
            f64:32:64-f80:32-n8:16:32-S128"
            .into(),
        arch: "x86".into(),
        options: base,
    }
}
