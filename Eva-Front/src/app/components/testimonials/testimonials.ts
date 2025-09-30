import { Component, signal } from '@angular/core';

type Testimonial = {
  quote: string;
  name: string;
  role: string;
  rating?: 1 | 2 | 3 | 4 | 5;
};

@Component({
  selector: 'app-testimonials',
  imports: [],
  templateUrl: './testimonials.html',
  styleUrl: './testimonials.scss',
})
export class Testimonials {
  title = signal('Lo que dicen nuestros clientes');
  subtitle = signal('Historias reales de empresas que transformaron su reclutamiento');

  // MOCK: data fija
  items = signal<Testimonial[]>([
    {
      quote:
        '“Evalyze transformó nuestro proceso de selección. Ahora podemos evaluar 10 veces más candidatos con mayor precisión.”',
      name: 'María González',
      role: 'Directora de RRHH en TechCorp',
      rating: 5,
    },
    {
      quote:
        '“La IA de Evalyze identificó talentos que habríamos pasado por alto. Una inversión que se paga sola.”',
      name: 'Carlos Mendez',
      role: 'CEO en StartupX',
      rating: 5,
    },
    {
      quote:
        '“Los informes de compatibilidad son increíblemente detallados. Tomamos mejores decisiones de contratación.”',
      name: 'Ana Rodríguez',
      role: 'Talent Acquisition Manager en GlobalTech',
      rating: 5,
    },
  ]);

  stars(n = 0): number[] {
    return Array.from({ length: n }, (_, i) => i);
  }
}
