import { Component, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormsModule, NgForm } from '@angular/forms';

@Component({
  selector: 'app-ver-demo',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './ver-demo.html',
  styleUrls: ['./ver-demo.scss']
})
export class VerDemo {
  email = '';
  password = '';
  remember = false;
  loading = false;
  error: string | null = null;

  constructor(private router: Router, private zone: NgZone) {}

  async login(form: NgForm): Promise<void> {
    this.error = null;
    const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email.trim());
    if (!ok) { this.error = 'Ingresa un email válido'; return; }

    this.loading = true;
    try {
      const success = await this.zone.run(() => this.router.navigateByUrl('/panel'));
      if (!success && typeof window !== 'undefined') window.location.assign('/panel');
    } catch (e: any) {
      this.error = e?.message || 'No se pudo iniciar sesión';
    } finally {
      this.loading = false;
    }
  }
}
