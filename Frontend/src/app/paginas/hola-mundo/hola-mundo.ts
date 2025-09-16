import {
  Component, NgZone, HostListener, AfterViewInit,
  Inject, PLATFORM_ID
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-hola-mundo',
  standalone: true,
  imports: [CommonModule, HttpClientModule, RouterLink],
  templateUrl: './hola-mundo.html',
  styleUrls: ['./hola-mundo.scss']
})
export class HolaMundo implements AfterViewInit {
  respuesta: string | null = null;
  cargando = false;
  error: string | null = null;

  private sectionIds = ['caracteristicas', 'beneficios', 'testimonios', 'cta'];
  active: 'caracteristicas' | 'beneficios' | 'testimonios' | 'cta' | null = null;
  private readonly isBrowser: boolean;

  constructor(private ngZone: NgZone, @Inject(PLATFORM_ID) platformId: Object) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngAfterViewInit(): void {
    if (!this.isBrowser) return;
    this.onScroll();
  }

  @HostListener('window:scroll', [])
  onScroll(): void {
    if (!this.isBrowser) return;
    const offset = 120;
    const y = window.scrollY + offset;

    let current: typeof this.active = null;
    for (const id of this.sectionIds) {
      const el = document.getElementById(id);
      if (!el) continue;
      const top = el.getBoundingClientRect().top + window.scrollY;
      if (y >= top) current = id as typeof this.active;
    }
    this.active = current;
  }

  async conectarBackend(): Promise<void> {
    this.cargando = true;
    this.error = null;
    this.respuesta = null;

    try {
      const resp = await fetch('https://localhost:9000'); // cambia por tu API
      if (!resp.ok) throw new Error('Error en la respuesta del servidor');
      const data = await resp.json();
      this.ngZone.run(() => {
        this.respuesta = JSON.stringify(data);
        this.cargando = false;
      });
    } catch (e: any) {
      this.ngZone.run(() => {
        this.error = e?.message || 'Error desconocido';
        this.cargando = false;
      });
    }
  }
}
