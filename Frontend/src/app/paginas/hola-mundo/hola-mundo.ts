import { Component, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-hola-mundo',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  templateUrl: './hola-mundo.html',
  styleUrls: ['./hola-mundo.scss']
})
export class HolaMundo {
  respuesta: string | null = null;
  cargando = false;
  error: string | null = null;

  constructor(private ngZone: NgZone) {}

  async conectarBackend(): Promise<void> {
    this.cargando = true;
    this.error = null;
    this.respuesta = null;

    try {
      // Cambia la URL por la de tu API real
      const resp = await fetch('https://jsonplaceholder.typicode.com/todos/1');
      if (!resp.ok) throw new Error('Error en la respuesta del servidor');
      const data = await resp.json();
      this.ngZone.run(() => {
        this.respuesta = JSON.stringify(data);
        this.cargando = false;
      });
    } catch (e: any) {
      this.ngZone.run(() => {
        this.error = e.message || 'Error desconocido';
        this.cargando = false;
      });
    }
  }
}
