import { Component, Output, EventEmitter, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router'; // <--- 1. Importamos RouterLink

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink], // <--- 2. Lo agregamos aquí para poder usarlo en el HTML
  templateUrl: './navbar.html',
  styleUrl: './navbar.scss',
})
export class Navbar {
  menuOpen = false;
  private router = inject(Router);

  @Output() openLogin = new EventEmitter<void>();
  @Output() openSignup = new EventEmitter<void>();

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  closeMenu() {
    this.menuOpen = false;
  }

  handleLogin() {
    this.closeMenu();
    this.router.navigate(['/auth']); // Ruta para Iniciar Sesión
  }

  handleSignup() {
    this.closeMenu();
    // 3. CAMBIO: Redirigir a la ruta de registro en lugar de auth
    this.router.navigate(['/register']); 
  }
}