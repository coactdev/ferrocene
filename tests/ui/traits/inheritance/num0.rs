// run-pass
#![allow(dead_code)]
// Extending Num and using inherited static methods

// pretty-expanded FIXME #23616

use std::cmp::PartialOrd;

pub trait NumCast: Sized {
    fn from(i: i32) -> Option<Self>;
}

pub trait Num {
    fn from_int(i: isize) -> Self;
    fn gt(&self, other: &Self) -> bool;
}

pub trait NumExt: NumCast + PartialOrd { }

fn greater_than_one<T:NumExt>(n: &T) -> bool {
    n.gt(&NumCast::from(1).unwrap())
}

pub fn main() {}

// ferrocene-annotations: fls_xa4nbfas01cj
// Call Expressions
