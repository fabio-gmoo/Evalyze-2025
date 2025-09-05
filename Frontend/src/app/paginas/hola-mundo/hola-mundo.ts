import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-hola-mundo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hola-mundo.html',
  styleUrl: './hola-mundo.scss'
})
export class HolaMundo {
  respuesta: string | null = null;

  constructor(private cdr: ChangeDetectorRef) {}

  async conectarBackend() {
    this.respuesta = null;
    // Simulación de llamada a backend, reemplaza por tu lógica real
    setTimeout(() => {
      this.respuesta = '¡Respuesta recibida del backend!';
      this.cdr.detectChanges();
    }, 1500);
  }
}
