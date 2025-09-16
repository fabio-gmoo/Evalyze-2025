import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-ver-demo',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './ver-demo.html',
  styleUrls: ['./ver-demo.scss']
})
export class VerDemo {}
