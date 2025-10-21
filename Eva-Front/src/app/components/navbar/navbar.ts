import { Component, Output, EventEmitter, inject } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-navbar',
  imports: [],
  templateUrl: './navbar.html',
  styleUrl: './navbar.scss',
})
export class Navbar {
  menuOpen = false;
  private router = inject(Router);

  // Cambiar los nombres para que coincidan con home.html
  @Output() openLogin = new EventEmitter<void>();
  @Output() openSignup = new EventEmitter<void>();

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  closeMenu() {
    this.menuOpen = false;
  }

  handleLogin() {
    //this.openLogin.emit();
    //this.closeMenu();
    this.router.navigate(['/auth']);
  }

  handleSignup() {
    //this.openSignup.emit();

    //this.closeMenu();
    this.router.navigate(['/auth']);
  }
}
