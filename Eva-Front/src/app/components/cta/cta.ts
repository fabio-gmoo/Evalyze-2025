import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-cta',
  imports: [],
  templateUrl: './cta.html',
  styleUrl: './cta.scss',
})
export class Cta {
  title = signal('¿Listo para revolucionar tu reclutamiento?');
  subtitle = signal('Únete a cientos de empresas que ya están contratando mejor con Evalyze');
}
