import { Component, signal } from '@angular/core';
import { Navbar } from '@components/navbar/navbar';
import { Hero } from '@components/hero/hero';
import { Features } from '@components/features/features';
import { Benefits } from '@components/benefits/benefits';
import { Testimonials } from '@components/testimonials/testimonials';
import { Cta } from '@components/cta/cta';
import { Footer } from '@components/footer/footer';
import { Auth } from '@pages/auth/auth';

type Mode = 'login' | 'signup';

@Component({
  selector: 'app-home',
  imports: [Navbar, Hero, Features, Benefits, Testimonials, Cta, Footer, Auth],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  showAuth = signal(false);
  authMode = signal<Mode>('login');

  openAuth(mode: Mode) {
    this.authMode.set(mode);
    this.showAuth.set(true);

    document.body.style.overflow = 'hidden';
  }

  closeAuth() {
    this.showAuth.set(false);
    document.body.style.overflow = '';
  }

  // Método para manejar el login exitoso
  onLoginSuccess() {
    this.closeAuth();
  }
}
