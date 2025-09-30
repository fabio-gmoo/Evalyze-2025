import { Component, EventEmitter, Output, signal } from '@angular/core';
import { Registerform } from '@widgets/registerform/registerform';

@Component({
  selector: 'app-register',
  imports: [Registerform],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class Register {
  @Output() loginClick = new EventEmitter<void>();
  reasons = signal([
    '14 días de prueba gratuita',
    'Sin tarjeta de crédito requerida',
    'Configuración en menos de 5 minutos',
    'Soporte dedicado incluido',
  ]);
}
