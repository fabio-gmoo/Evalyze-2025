import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Vacante {
  titulo: string;
  departamento: string;
  ubicacion: string;
  contrato: string;
  salarioMin: number;
  salarioMax: number;
  descripcion: string;
  requisitos: string;
  responsabilidades: string;
  duracionMin: number;
  puntajeMin: number;
  preguntas: { texto: string; tipo: string; peso: number; keywords: string }[];
}

@Injectable({
  providedIn: 'root',
})
export class Vacante {
  private apiUrl = 'http://localhost:8000/vacantes/guardar/'; // URL de la API donde se guardará la vacante

  constructor(private http: HttpClient) {}

  // Método para guardar la vacante
  crearVacante(vacante: Vacante): Observable<any> {
    return this.http.post(this.apiUrl, vacante);
  }
}
