//! Tampon possédé, grossi par réallocation.
//!
//! L'API est safe. L'intérieur alloue, écrit et libère.
//! `push` panique si la capacité ne tient plus dans un `usize` ou dans `isize`.
//! Une allocation refusée par le système interrompt le processus (`handle_alloc_error`).

use std::alloc::{Layout, alloc, dealloc, handle_alloc_error, realloc};
use std::fmt;
use std::marker::PhantomData;
use std::mem;
use std::ptr::{self, NonNull};

pub struct Buf<T> {
    ptr: NonNull<T>,
    len: usize,
    cap: usize,
    _owned: PhantomData<T>,
}

impl<T> Buf<T> {
    pub fn new() -> Self {
        Self {
            ptr: NonNull::dangling(),
            len: 0,
            cap: if mem::size_of::<T>() == 0 {
                usize::MAX
            } else {
                0
            },
            _owned: PhantomData,
        }
    }

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    pub fn capacity(&self) -> usize {
        self.cap
    }

    pub fn push(&mut self, value: T) {
        if self.len == self.cap {
            self.grow();
        }
        assert!(self.len < self.cap, "plus de place après agrandissement");
        unsafe {
            // SAFETY: len < cap, le créneau len n'est pas initialisé, le bloc
            // couvre cap éléments, &mut self écarte toute autre référence.
            // Pour un ZST, add ne déplace pas l'adresse et write n'y lit rien.
            ptr::write(self.ptr.as_ptr().add(self.len), value);
        }
        self.len += 1;
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        unsafe {
            // SAFETY: l'index était initialisé avant le décrément.
            // read emporte la valeur. Drop ne la détruira pas une seconde fois.
            Some(ptr::read(self.ptr.as_ptr().add(self.len)))
        }
    }

    pub fn get(&self, index: usize) -> Option<&T> {
        if index >= self.len {
            return None;
        }
        unsafe {
            // SAFETY: index < len, ce créneau est initialisé, &self interdit
            // un &mut en même temps. add reste dans le bloc (index < cap).
            Some(&*self.ptr.as_ptr().add(index))
        }
    }

    pub fn get_mut(&mut self, index: usize) -> Option<&mut T> {
        if index >= self.len {
            return None;
        }
        unsafe {
            // SAFETY: index < len, créneau initialisé, &mut self est l'unique
            // accès le temps de la référence rendue.
            Some(&mut *self.ptr.as_ptr().add(index))
        }
    }

    pub fn as_slice(&self) -> &[T] {
        unsafe {
            // SAFETY: len éléments initialisés, pointeur aligné et non nul.
            // Un ZST ou un tampon vide utilise le dangling de NonNull, valide
            // pour une longueur nulle ou une taille nulle.
            &*ptr::slice_from_raw_parts(self.ptr.as_ptr(), self.len)
        }
    }

    fn grow(&mut self) {
        assert!(mem::size_of::<T>() != 0, "un ZST ne réalloue pas");
        let new_cap = if self.cap == 0 {
            4
        } else {
            self.cap
                .checked_mul(2)
                .expect("la capacité ne tient plus dans un usize")
        };
        let new_layout =
            Layout::array::<T>(new_cap).expect("la taille du tampon dépasse isize::MAX");
        let new_ptr = if self.cap == 0 {
            unsafe {
                // SAFETY: T n'est pas un ZST et new_cap vaut 4, la taille est non nulle.
                alloc(new_layout)
            }
        } else {
            let old_layout = Layout::array::<T>(self.cap).expect("l'ancienne taille était valide");
            unsafe {
                // SAFETY: old_layout est celui de l'allocation vivante, la nouvelle
                // taille est non nulle, &mut self donc aucune référence ne vit.
                realloc(self.ptr.as_ptr().cast(), old_layout, new_layout.size())
            }
        };
        if new_ptr.is_null() {
            handle_alloc_error(new_layout);
        }
        unsafe {
            // SAFETY: new_ptr vient d'être testé non nul.
            self.ptr = NonNull::new_unchecked(new_ptr.cast());
        }
        self.cap = new_cap;
    }
}

// SAFETY: NonNull est !Send parce qu'un pointeur nu peut aliaser.
// Ici le tampon possède le bloc, et l'envoyer déplace le seul pointeur.
// Les éléments partent avec lui, donc T: Send suffit.
unsafe impl<T: Send> Send for Buf<T> {}

// SAFETY: &Buf ne produit que des &T (get, as_slice), sans mutabilité
// intérieure. &mut Buf reste exclusif. T: Sync suffit.
unsafe impl<T: Sync> Sync for Buf<T> {}

impl<T> Default for Buf<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: fmt::Debug> fmt::Debug for Buf<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_list().entries(self.as_slice()).finish()
    }
}

impl<T> Drop for Buf<T> {
    fn drop(&mut self) {
        unsafe {
            // SAFETY: exactement les len premiers éléments sont initialisés.
            // drop_in_place les détruit une fois. Le reste de la capacité ne l'est pas.
            if self.len > 0 {
                ptr::drop_in_place(ptr::slice_from_raw_parts_mut(self.ptr.as_ptr(), self.len));
            }
        }
        if mem::size_of::<T>() == 0 || self.cap == 0 {
            return;
        }
        let layout = Layout::array::<T>(self.cap).expect("l'allocation a ce layout");
        unsafe {
            // SAFETY: ptr vient de alloc ou realloc avec ce layout.
            // Les éléments sont déjà détruits. Plus aucune référence.
            dealloc(self.ptr.as_ptr().cast(), layout);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::Buf;
    use std::cell::Cell;
    use std::rc::Rc;

    #[test]
    fn empty_pop() {
        let mut buf = Buf::<u32>::new();
        assert!(buf.is_empty());
        assert_eq!(buf.capacity(), 0);
        assert_eq!(buf.pop(), None);
        assert!(buf.get(0).is_none());
        assert!(buf.as_slice().is_empty());
    }

    #[test]
    fn one_push_pop() {
        let mut buf = Buf::new();
        buf.push(7u8);
        assert_eq!(buf.len(), 1);
        assert_eq!(buf.get(0), Some(&7));
        assert_eq!(buf.as_slice(), &[7]);
        assert_eq!(buf.pop(), Some(7));
        assert!(buf.is_empty());
        assert!(buf.capacity() >= 4);
    }

    #[test]
    fn grows_past_four() {
        let mut buf = Buf::new();
        for value in 0..5 {
            buf.push(value);
        }
        assert!(buf.capacity() >= 5);
        assert_eq!(buf.as_slice(), &[0, 1, 2, 3, 4]);
        *buf.get_mut(4).unwrap() = 9;
        assert_eq!(buf.get(4), Some(&9));
        assert_eq!(buf.get(5), None);
    }

    #[test]
    fn drop_count() {
        let hits = Rc::new(Cell::new(0));
        struct Bomb(Rc<Cell<u32>>);
        impl Drop for Bomb {
            fn drop(&mut self) {
                self.0.set(self.0.get() + 1);
            }
        }
        let mut buf = Buf::new();
        for _ in 0..5 {
            buf.push(Bomb(Rc::clone(&hits)));
        }
        assert!(buf.pop().is_some());
        assert_eq!(hits.get(), 1);
        drop(buf);
        assert_eq!(hits.get(), 5);
    }

    struct Empty;

    #[test]
    fn zst_push_pop() {
        let mut buf = Buf::new();
        assert_eq!(buf.capacity(), usize::MAX);
        for _ in 0..10 {
            buf.push(Empty);
        }
        assert_eq!(buf.len(), 10);
        assert_eq!(buf.as_slice().len(), 10);
        assert!(buf.pop().is_some());
        assert_eq!(buf.len(), 9);
    }

    #[test]
    fn zst_drop() {
        let hits = Rc::new(Cell::new(0));
        struct Tick(Rc<Cell<u32>>);
        impl Drop for Tick {
            fn drop(&mut self) {
                self.0.set(self.0.get() + 1);
            }
        }
        let mut buf = Buf::new();
        buf.push(Tick(Rc::clone(&hits)));
        buf.push(Tick(Rc::clone(&hits)));
        drop(buf);
        assert_eq!(hits.get(), 2);
    }

    #[test]
    fn send_sync_u8() {
        fn need<T: Send + Sync>() {}
        need::<Buf<u8>>();
    }
}
