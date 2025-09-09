import { Component, signal, effect } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { AiService, Health, ChatResponse } from '../../services/ai-service';

@Component({
  selector: 'app-hola-mundo',
  standalone: true,
  imports: [],
  templateUrl: './hola-mundo.html',
  styleUrls: ['./hola-mundo.scss'],
})
export class HolaMundo {
  respuesta = signal<string | null>(null);
  error = signal<string | null>(null);
  cargando = signal(false);

  constructor(private ai: AiService) {
    effect(() => {});
  }

  private toErrorMessage(e: unknown): string {
    // Narrowing: ¿es un HttpErrorResponse?
    if (e instanceof HttpErrorResponse) {
      const err = e.error as any; // backend puede devolver string u objeto
      if (typeof err === 'string') return err;

      const detail = err?.detail ?? err?.message ?? null;
      if (detail) return String(detail);

      return `HTTP ${e.status} ${e.statusText ?? ''}`.trim();
    }

    // ¿Es un Error normal?
    if (e instanceof Error) return e.message;

    // Último recurso: serializar
    try {
      return JSON.stringify(e);
    } catch {
      return String(e);
    }
  }
  conectarBackend(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.respuesta.set(null);
    this.ai.health().subscribe({
      next: (d: Health) => {
        this.respuesta.set(JSON.stringify(d, null, 2));
        this.cargando.set(false);
      },
      error: (e: unknown) => {
        this.error.set(this.toErrorMessage(e));
        this.cargando.set(false);
      },
    });
  }
  enviarChatDemo(mensaje: string): void {
    this.cargando.set(true);
    this.error.set(null);
    this.respuesta.set(null);
    this.ai.demoChat(mensaje).subscribe({
      next: (d: ChatResponse) => {
        this.respuesta.set(d.reply);
        this.cargando.set(false);
      },
      error: (e: unknown) => {
        this.error.set(this.toErrorMessage(e));
        this.cargando.set(false);
      },
    });
  }
  enviarChat(mensaje: string): void {
    this.cargando.set(true);
    this.error.set(null);
    this.respuesta.set(null);
    const jwt = localStorage.getItem('access'); // por ejemplo, lo guardas tras login
    this.ai.chat(mensaje, 'front-dev-1', jwt ?? undefined).subscribe({
      next: (d) => {
        this.respuesta.set(d.reply);
        this.cargando.set(false);
      },
      error: (e) => {
        this.error.set(e instanceof Error ? e.message : String(e));
        this.cargando.set(false);
      },
    });
  }
}
