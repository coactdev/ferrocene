fn f1<'a>(x: u8, y: &'a ...) {}
//~^ ERROR C-variadic type `...` may not be nested inside another type

fn f2<'a>(x: u8, y: Vec<&'a ...>) {}
//~^ ERROR C-variadic type `...` may not be nested inside another type

fn main() {
    let _recovery_witness: () = 0; //~ ERROR mismatched types
}

// ferrocene-annotations: fls_qcb1n9c0e5hz
// Functions
