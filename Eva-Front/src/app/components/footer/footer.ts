import { Component, signal } from '@angular/core';

type Link = { label: string; href: string };

@Component({
  selector: 'app-footer',
  imports: [],
  templateUrl: './footer.html',
  styleUrl: './footer.scss',
})
export class Footer {
  year = signal(new Date().getFullYear());
  product = signal<Link[]>([
    { label: 'Características', href: '#caracteristicas' },
    { label: 'Precios', href: '#' },
    { label: 'Integraciones', href: '#' },
    { label: 'API', href: '#' },
  ]);

  company = signal<Link[]>([
    { label: 'Acerca de', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Carreras', href: '#' },
    { label: 'Contacto', href: '#' },
  ]);

  support = signal<Link[]>([
    { label: 'Centro de ayuda', href: '#' },
    { label: 'Documentación', href: '#' },
    { label: 'Estado del servicio', href: '#' },
    { label: 'Seguridad', href: '#' },
  ]);
}
