import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-navbar',
  imports: [],
  templateUrl: './navbar.html',
  styleUrl: './navbar.scss',
})
export class Navbar {
  menuOpen = false;

  // Cambiar los nombres para que coincidan con home.html
  @Output() openLogin = new EventEmitter<void>();
  @Output() openSignup = new EventEmitter<void>();

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  closeMenu() {
    this.menuOpen = false;
  }
}
